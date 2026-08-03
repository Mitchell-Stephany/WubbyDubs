from typing import Dict, Optional, List
from .advanced_base import AdvancedScraper
from .base import validate_product_id

class AdvancedHomeDepotScraper(AdvancedScraper):
    """Advanced Home Depot scraper with anti-detection"""
    
    BASE_URL = "https://www.homedepot.com"
    
    def get_product_price(self, product_id: str) -> Optional[float]:
        """Get current price for a product using product ID"""
        if not self.driver:
            return None
            
        try:
            url = f"{self.BASE_URL}/p/{validate_product_id(product_id)}"
            self.driver.get(url)
            self._random_delay(3, 6)
            
            # Try multiple price selectors
            price_selectors = [
                (By.CSS_SELECTOR, '[data-testid="product-price"]'),
                (By.CSS_SELECTOR, '.price__format'),
                (By.CSS_SELECTOR, '.price-dollars'),
                (By.CSS_SELECTOR, '.price-cents'),
                (By.CSS_SELECTOR, '.product-price'),
                (By.XPATH, '//div[contains(@class, "price")]'),
            ]
            
            for by, selector in price_selectors:
                try:
                    price_text = self._safe_get_element_text(by, selector, timeout=5)
                    if price_text:
                        price_text = price_text.replace('$', '').replace(',', '').strip()
                        try:
                            return float(price_text)
                        except ValueError:
                            continue
                except:
                    continue
            
            return None
            
        except Exception as e:
            print(f"Error fetching Home Depot price for {product_id}: {e}")
            return None
    
    def get_product_info(self, product_id: str) -> Dict:
        """Get detailed product information"""
        if not self.driver:
            return {}
            
        try:
            url = f"{self.BASE_URL}/p/{validate_product_id(product_id)}"
            self.driver.get(url)
            self._random_delay(3, 6)
            
            # Extract product name
            name = self._safe_get_element_text(By.CSS_SELECTOR, 'h1.product-title', timeout=10)
            if not name:
                name = self._safe_get_element_text(By.TAG_NAME, 'h1', timeout=10)
            
            # Extract price
            price = self.get_product_price(product_id)
            
            # Extract category from breadcrumb
            category = "Unknown"
            try:
                category_elements = self.driver.find_elements(By.CSS_SELECTOR, '.breadcrumb a')
                if category_elements:
                    category = category_elements[-1].text.strip()
            except:
                pass
            
            return {
                'name': name or "Unknown",
                'url': url,
                'category': category,
                'price': price,
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
            url = f"{self.BASE_URL}/s/{query}"
            self.driver.get(url)
            self._random_delay(3, 5)
            
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
                    if '/p/' in product_url:
                        product_id = product_url.split('/p/')[-1].split('/')[0]
                    else:
                        continue
                    
                    # Extract name
                    name_element = card.find_element(By.CSS_SELECTOR, '.product-pod__title')
                    name = name_element.text.strip() if name_element else "Unknown"
                    
                    # Extract price
                    price = None
                    try:
                        price_element = card.find_element(By.CSS_SELECTOR, '.price__format')
                        price_text = price_element.text.strip()
                        price_text = price_text.replace('$', '').replace(',', '')
                        try:
                            price = float(price_text)
                        except ValueError:
                            pass
                    except:
                        pass
                    
                    products.append({
                        'product_id': product_id,
                        'name': name,
                        'url': f"{self.BASE_URL}{product_url}",
                        'category': category or 'Unknown',
                        'price': price,
                        'retailer': 'homedepot'
                    })
                    
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
        popular_searches = [
            'tools', 'appliances', 'kitchen', 'bathroom', 
            'lighting', 'flooring', 'paint', 'lawn'
        ]
        
        search_term = category if category != 'all' else popular_searches[0]
        return self.search_products(search_term, category, limit)