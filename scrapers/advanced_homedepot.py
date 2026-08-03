from typing import Dict, Optional, List
from selenium.webdriver.common.by import By
from .advanced_base import AdvancedScraper
from utils import build_product_record, pick_search_term

class AdvancedHomeDepotScraper(AdvancedScraper):
    """Advanced Home Depot scraper with anti-detection"""
    
    BASE_URL = "https://www.homedepot.com"
    
    PRICE_SELECTORS = [
        (By.CSS_SELECTOR, '[data-testid="product-price"]'),
        (By.CSS_SELECTOR, '.price__format'),
        (By.CSS_SELECTOR, '.price-dollars'),
        (By.CSS_SELECTOR, '.price-cents'),
        (By.CSS_SELECTOR, '.product-price'),
        (By.XPATH, '//div[contains(@class, "price")]'),
    ]
    
    POPULAR_SEARCHES = [
        'tools', 'appliances', 'kitchen', 'bathroom',
        'lighting', 'flooring', 'paint', 'lawn'
    ]
    
    def get_product_price(self, product_id: str) -> Optional[float]:
        """Get current price for a product using product ID"""
        if not self.driver:
            return None
            
        try:
            self._load_page(f"{self.BASE_URL}/p/{product_id}")
            return self._find_price(self.PRICE_SELECTORS)
            
        except Exception as e:
            print(f"Error fetching Home Depot price for {product_id}: {e}")
            return None
    
    def get_product_info(self, product_id: str) -> Dict:
        """Get detailed product information"""
        if not self.driver:
            return {}
            
        try:
            url = f"{self.BASE_URL}/p/{product_id}"
            self._load_page(url)
            
            name = self._safe_get_element_text(By.CSS_SELECTOR, 'h1.product-title', timeout=10)
            if not name:
                name = self._safe_get_element_text(By.TAG_NAME, 'h1', timeout=10)
            
            return {
                'name': name or "Unknown",
                'url': url,
                'category': self._last_element_text(By.CSS_SELECTOR, '.breadcrumb a'),
                'price': self.get_product_price(product_id),
                'description': ''
            }
            
        except Exception as e:
            print(f"Error fetching Home Depot product info for {product_id}: {e}")
            return {}
    
    def search_products(self, query: str, category: str = None, limit: int = 20) -> List[Dict]:
        """Search for products on Home Depot"""
        if not self.driver:
            return []
            
        try:
            self._load_page(f"{self.BASE_URL}/s/{query}", 3, 5)
            
            products = []
            product_cards = self.driver.find_elements(By.CSS_SELECTOR, '.product-pod')
            
            for card in product_cards[:limit]:
                try:
                    # Extract product ID from URL
                    link_element = card.find_element(By.CSS_SELECTOR, 'a.product-pod__link')
                    if not link_element:
                        continue
                    
                    product_url = link_element.get_attribute('href')
                    # Extract ID from URL (usually after /p/)
                    if '/p/' not in product_url:
                        continue
                    product_id = product_url.split('/p/')[-1].split('/')[0]
                    
                    products.append(build_product_record(
                        product_id=product_id,
                        name=self._element_text(card, By.CSS_SELECTOR, '.product-pod__title'),
                        url=f"{self.BASE_URL}{product_url}",
                        category=category,
                        price=self._element_price(card, By.CSS_SELECTOR, '.price__format'),
                        retailer='homedepot'
                    ))
                    
                    self._random_delay(0.5, 1.5)  # Small delay between products
                    
                except Exception as e:
                    print(f"Error parsing Home Depot product card: {e}")
                    continue
            
            return products
            
        except Exception as e:
            print(f"Error searching Home Depot products: {e}")
            return []
    
    def get_trending_products(self, category: str = 'all', limit: int = 20) -> List[Dict]:
        """Get trending products from Home Depot"""
        return self.search_products(pick_search_term(category, self.POPULAR_SEARCHES), category, limit)
