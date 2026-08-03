from typing import Dict, Optional, List
from .advanced_base import AdvancedScraper
from .base import validate_product_id

class AdvancedTargetScraper(AdvancedScraper):
    """Advanced Target scraper with anti-detection"""
    
    BASE_URL = "https://www.target.com"
    
    def get_product_price(self, product_id: str) -> Optional[float]:
        """Get current price for a product using TCIN"""
        if not self.driver:
            return None
            
        try:
            url = f"{self.BASE_URL}/p/{validate_product_id(product_id)}"
            self.driver.get(url)
            self._random_delay(3, 6)
            
            # Try multiple price selectors
            price_selectors = [
                (By.CSS_SELECTOR, '[data-test="product-price"]'),
                (By.CSS_SELECTOR, '.Price-characteristic'),
                (By.CSS_SELECTOR, '.style__PriceText___2HiQw'),
                (By.CSS_SELECTOR, 'span[data-test="product-price"]'),
                (By.XPATH, '//span[contains(@class, "Price")]'),
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
            print(f"Error fetching Target price for {product_id}: {e}")
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
            name = self._safe_get_element_text(By.CSS_SELECTOR, '[data-test="product-title"]', timeout=10)
            if not name:
                name = self._safe_get_element_text(By.TAG_NAME, 'h1', timeout=10)
            
            # Extract price
            price = self.get_product_price(product_id)
            
            # Extract category from breadcrumb
            category = "Unknown"
            try:
                breadcrumbs = self.driver.find_elements(By.CSS_SELECTOR, '[data-test="breadcrumb"] a')
                if breadcrumbs:
                    category = breadcrumbs[-1].text.strip()
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
            print(f"Error fetching Target product info for {product_id}: {e}")
            return {}
    
    def search_products(self, query: str, category: str = None, limit: int = 20) -> List[Dict]:
        """Search for products on Target"""
        if not self.driver:
            return []
            
        try:
            url = f"{self.BASE_URL}/s"
            self.driver.get(url)
            self._random_delay(2, 4)
            
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
                    
                    # Extract name
                    name_element = card.find_element(By.CSS_SELECTOR, '[data-test="product-title"]')
                    name = name_element.text.strip() if name_element else "Unknown"
                    
                    # Extract price
                    price = None
                    try:
                        price_element = card.find_element(By.CSS_SELECTOR, '[data-test="product-price"]')
                        price_text = price_element.text.strip()
                        price_text = price_text.replace('$', '').replace(',', '')
                        try:
                            price = float(price_text)
                        except ValueError:
                            pass
                    except:
                        pass
                    
                    # Extract URL
                    link_element = card.find_element(By.CSS_SELECTOR, 'a[href*="/p/"]')
                    product_url = f"{self.BASE_URL}{link_element.get_attribute('href')}" if link_element else f"{self.BASE_URL}/p/{tcin}"
                    
                    products.append({
                        'product_id': tcin,
                        'name': name,
                        'url': product_url,
                        'category': category or 'Unknown',
                        'price': price,
                        'retailer': 'target'
                    })
                    
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
        popular_searches = [
            'electronics', 'home goods', 'kitchen', 'furniture', 
            'toys', 'beauty', 'clothing', 'appliances'
        ]
        
        search_term = category if category != 'all' else popular_searches[0]
        return self.search_products(search_term, category, limit)