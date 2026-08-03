from typing import Dict, Optional, List
from urllib.parse import quote
import requests
from bs4 import BeautifulSoup
from .base import BaseScraper, validate_product_id

class HomeDepotScraper(BaseScraper):
    """Home Depot web scraper"""
    
    BASE_URL = "https://www.homedepot.com"
    
    def __init__(self, config):
        super().__init__(config)
    
    def get_product_price(self, product_id: str) -> Optional[float]:
        """Get current price for a product using product ID"""
        try:
            url = f"{self.BASE_URL}/p/{validate_product_id(product_id)}"
            response = requests.get(url, headers=self._get_headers(), timeout=self.REQUEST_TIMEOUT)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'lxml')
            
            # Home Depot price selectors
            price_selectors = [
                '[data-testid="product-price"]',
                '.price__format',
                '.price-dollars',
                '.price-cents',
                '.product-price'
            ]
            
            for selector in price_selectors:
                price_element = soup.select_one(selector)
                if price_element:
                    price_text = price_element.get_text().strip()
                    # Handle formats like "$123.45" or split dollars/cents
                    price_text = price_text.replace('$', '').replace(',', '')
                    try:
                        return float(price_text)
                    except ValueError:
                        continue
            
        except Exception as e:
            print(f"Error fetching Home Depot price for {product_id}: {e}")
        return None
    
    def get_product_info(self, product_id: str) -> Dict:
        """Get detailed product information"""
        try:
            url = f"{self.BASE_URL}/p/{validate_product_id(product_id)}"
            response = requests.get(url, headers=self._get_headers(), timeout=self.REQUEST_TIMEOUT)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'lxml')
            
            # Extract product name
            name_element = soup.select_one('h1.product-title')
            name = name_element.get_text().strip() if name_element else "Unknown"
            
            # Extract price
            price = self.get_product_price(product_id)
            
            # Extract category from breadcrumb
            category_elements = soup.select('.breadcrumb a')
            category = category_elements[-1].get_text().strip() if category_elements else "Unknown"
            
            return {
                'name': name,
                'url': url,
                'category': category,
                'price': price,
                'description': ''
            }
            
        except Exception as e:
            print(f"Error fetching Home Depot product info for {product_id}: {e}")
        return {}
    
    def search_products(self, query: str, category: str = None) -> List[Dict]:
        """Search for products on Home Depot"""
        try:
            url = f"{self.BASE_URL}/s/{quote(query, safe='')}"
            params = {
                'NCNI-5': '1',
                'Nao-': '1',
                'Ns': None,  # Sort parameter
                'M': None    # Category filter
            }
            
            if category:
                params['M'] = category
            
            response = requests.get(url, params=params, headers=self._get_headers(), timeout=self.REQUEST_TIMEOUT)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'lxml')
            products = []
            
            # Home Depot product cards
            product_cards = soup.select('.product-pod')
            
            for card in product_cards[:20]:  # Limit to 20 results
                try:
                    # Extract product ID from URL
                    link_element = card.select_one('a.product-pod__link')
                    if not link_element:
                        continue
                    
                    product_url = link_element['href']
                    # Extract ID from URL (usually after /p/)
                    if '/p/' in product_url:
                        product_id = product_url.split('/p/')[-1].split('/')[0]
                    else:
                        continue
                    
                    # Extract name
                    name_element = card.select_one('.product-pod__title')
                    name = name_element.get_text().strip() if name_element else "Unknown"
                    
                    # Extract price
                    price_element = card.select_one('.price__format')
                    price = None
                    if price_element:
                        price_text = price_element.get_text().strip()
                        price_text = price_text.replace('$', '').replace(',', '')
                        try:
                            price = float(price_text)
                        except ValueError:
                            pass
                    
                    products.append({
                        'product_id': product_id,
                        'name': name,
                        'url': f"{self.BASE_URL}{product_url}",
                        'category': category or 'Unknown',
                        'price': price,
                        'retailer': 'homedepot'
                    })
                    
                except Exception as e:
                    print(f"Error parsing Home Depot product card: {e}")
                    continue
            
            return products
            
        except Exception as e:
            print(f"Error searching Home Depot products: {e}")
        return []
    
    def get_trending_products(self, category: str = 'all') -> List[Dict]:
        """Get trending products from Home Depot"""
        # Home Depot doesn't have a public trending API
        popular_searches = [
            'tools', 'appliances', 'kitchen', 'bathroom', 
            'lighting', 'flooring', 'paint', 'lawn'
        ]
        
        search_term = category if category != 'all' else popular_searches[0]
        return self.search_products(search_term, category)
