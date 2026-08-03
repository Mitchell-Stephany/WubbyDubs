from typing import Dict, Optional, List
import requests
from bs4 import BeautifulSoup
from .base import BaseScraper

class TargetScraper(BaseScraper):
    """Target web scraper"""
    
    BASE_URL = "https://www.target.com"
    
    def __init__(self, config):
        super().__init__(config)
    
    def get_product_price(self, product_id: str) -> Optional[float]:
        """Get current price for a product using TCIN (Target ID)"""
        try:
            url = f"{self.BASE_URL}/p/{product_id}"
            response = requests.get(url, headers=self._get_headers())
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'lxml')
            
            # Try to find price in various formats Target uses
            price_selectors = [
                '[data-test="product-price"]',
                '.Price-characteristic',
                '.style__PriceText___2HiQw',
                'span[data-test="product-price"]'
            ]
            
            for selector in price_selectors:
                price_element = soup.select_one(selector)
                if price_element:
                    price_text = price_element.get_text().strip()
                    # Remove currency symbols and convert to float
                    price_text = price_text.replace('$', '').replace(',', '')
                    try:
                        return float(price_text)
                    except ValueError:
                        continue
            
        except Exception as e:
            print(f"Error fetching Target price for {product_id}: {e}")
        return None
    
    def get_product_info(self, product_id: str) -> Dict:
        """Get detailed product information"""
        try:
            url = f"{self.BASE_URL}/p/{product_id}"
            response = requests.get(url, headers=self._get_headers())
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'lxml')
            
            # Extract product name
            name_element = soup.select_one('[data-test="product-title"]')
            name = name_element.get_text().strip() if name_element else "Unknown"
            
            # Extract price
            price = self.get_product_price(product_id)
            
            # Extract category from breadcrumb
            category_element = soup.select_one('[data-test="breadcrumb"]')
            category = "Unknown"
            if category_element:
                breadcrumbs = category_element.select('a')
                if breadcrumbs:
                    category = breadcrumbs[-1].get_text().strip()
            
            return {
                'name': name,
                'url': url,
                'category': category,
                'price': price,
                'description': ''
            }
            
        except Exception as e:
            print(f"Error fetching Target product info for {product_id}: {e}")
        return {}
    
    def search_products(self, query: str, category: str = None) -> List[Dict]:
        """Search for products on Target"""
        try:
            url = f"{self.BASE_URL}/s"
            params = {
                'searchTerm': query,
                'category': category,
                'sortName': 'bestselling'
            }
            
            response = requests.get(url, params=params, headers=self._get_headers())
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'lxml')
            products = []
            
            # Target product cards
            product_cards = soup.select('[data-test="product-card"]')
            
            for card in product_cards[:20]:  # Limit to 20 results
                try:
                    # Extract TCIN from data attribute
                    tcin = card.get('data-tcin')
                    if not tcin:
                        continue
                    
                    # Extract name
                    name_element = card.select_one('[data-test="product-title"]')
                    name = name_element.get_text().strip() if name_element else "Unknown"
                    
                    # Extract price
                    price_element = card.select_one('[data-test="product-price"]')
                    price = None
                    if price_element:
                        price_text = price_element.get_text().strip()
                        price_text = price_text.replace('$', '').replace(',', '')
                        try:
                            price = float(price_text)
                        except ValueError:
                            pass
                    
                    # Extract URL
                    link_element = card.select_one('a[href*="/p/"]')
                    product_url = f"{self.BASE_URL}{link_element['href']}" if link_element else f"{self.BASE_URL}/p/{tcin}"
                    
                    products.append({
                        'product_id': tcin,
                        'name': name,
                        'url': product_url,
                        'category': category or 'Unknown',
                        'price': price,
                        'retailer': 'target'
                    })
                    
                except Exception as e:
                    print(f"Error parsing Target product card: {e}")
                    continue
            
            return products
            
        except Exception as e:
            print(f"Error searching Target products: {e}")
        return []
    
    def get_trending_products(self, category: str = 'all') -> List[Dict]:
        """Get trending products from Target"""
        # Target doesn't have a public trending API, so we'll search popular terms
        popular_searches = [
            'electronics', 'home goods', 'kitchen', 'furniture', 
            'toys', 'beauty', 'clothing', 'appliances'
        ]
        
        search_term = category if category != 'all' else popular_searches[0]
        return self.search_products(search_term, category)
