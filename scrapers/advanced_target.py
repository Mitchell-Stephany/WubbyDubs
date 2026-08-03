from typing import Dict, Optional, List
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from .advanced_base import AdvancedScraper
from utils import build_product_record, pick_search_term

class AdvancedTargetScraper(AdvancedScraper):
    """Advanced Target scraper with anti-detection"""
    
    BASE_URL = "https://www.target.com"
    
    PRICE_SELECTORS = [
        (By.CSS_SELECTOR, '[data-test="product-price"]'),
        (By.CSS_SELECTOR, '.Price-characteristic'),
        (By.CSS_SELECTOR, '.style__PriceText___2HiQw'),
        (By.CSS_SELECTOR, 'span[data-test="product-price"]'),
        (By.XPATH, '//span[contains(@class, "Price")]'),
    ]
    
    POPULAR_SEARCHES = [
        'electronics', 'home goods', 'kitchen', 'furniture',
        'toys', 'beauty', 'clothing', 'appliances'
    ]
    
    def get_product_price(self, product_id: str) -> Optional[float]:
        """Get current price for a product using TCIN"""
        if not self.driver:
            return None
            
        try:
            self._load_page(f"{self.BASE_URL}/p/{product_id}")
            return self._find_price(self.PRICE_SELECTORS)
            
        except Exception as e:
            print(f"Error fetching Target price for {product_id}: {e}")
            return None
    
    def get_product_info(self, product_id: str) -> Dict:
        """Get detailed product information"""
        if not self.driver:
            return {}
            
        try:
            url = f"{self.BASE_URL}/p/{product_id}"
            self._load_page(url)
            
            name = self._safe_get_element_text(By.CSS_SELECTOR, '[data-test="product-title"]', timeout=10)
            if not name:
                name = self._safe_get_element_text(By.TAG_NAME, 'h1', timeout=10)
            
            return {
                'name': name or "Unknown",
                'url': url,
                'category': self._last_element_text(By.CSS_SELECTOR, '[data-test="breadcrumb"] a'),
                'price': self.get_product_price(product_id),
                'description': ''
            }
            
        except Exception as e:
            print(f"Error fetching Target product info for {product_id}: {e}")
            return {}
    
    def search_products(self, query: str, category: str = None, limit: int = 20) -> List[Dict]:
        """Search for products on Target"""
        if not self.driver:
            return []
            
        try:
            self._load_page(f"{self.BASE_URL}/s", 2, 4)
            
            # Find search input and enter query
            search_input = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, 'input[type="search"], input[name="searchTerm"]'))
            )
            search_input.clear()
            search_input.send_keys(query)
            self._random_delay(1, 2)
            
            # Submit search
            search_input.submit()
            self._random_delay(3, 5)
            
            products = []
            product_cards = self.driver.find_elements(By.CSS_SELECTOR, '[data-test="product-card"]')
            
            for card in product_cards[:limit]:
                try:
                    # Extract TCIN from data attribute
                    tcin = card.get_attribute('data-tcin')
                    if not tcin:
                        continue
                    
                    # Extract URL
                    link_element = card.find_element(By.CSS_SELECTOR, 'a[href*="/p/"]')
                    product_url = f"{self.BASE_URL}{link_element.get_attribute('href')}" if link_element else f"{self.BASE_URL}/p/{tcin}"
                    
                    products.append(build_product_record(
                        product_id=tcin,
                        name=self._element_text(card, By.CSS_SELECTOR, '[data-test="product-title"]'),
                        url=product_url,
                        category=category,
                        price=self._element_price(card, By.CSS_SELECTOR, '[data-test="product-price"]'),
                        retailer='target'
                    ))
                    
                    self._random_delay(0.5, 1.5)  # Small delay between products
                    
                except Exception as e:
                    print(f"Error parsing Target product card: {e}")
                    continue
            
            return products
            
        except Exception as e:
            print(f"Error searching Target products: {e}")
            return []
    
    def get_trending_products(self, category: str = 'all', limit: int = 20) -> List[Dict]:
        """Get trending products from Target"""
        return self.search_products(pick_search_term(category, self.POPULAR_SEARCHES), category, limit)
