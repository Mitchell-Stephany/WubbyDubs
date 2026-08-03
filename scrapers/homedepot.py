from typing import Dict, Optional, List
from .base import BaseScraper
from utils import build_product_record, parse_price, pick_search_term

class HomeDepotScraper(BaseScraper):
    """Home Depot web scraper"""
    
    BASE_URL = "https://www.homedepot.com"
    
    PRICE_SELECTORS = [
        '[data-testid="product-price"]',
        '.price__format',
        '.price-dollars',
        '.price-cents',
        '.product-price'
    ]
    
    POPULAR_SEARCHES = [
        'tools', 'appliances', 'kitchen', 'bathroom',
        'lighting', 'flooring', 'paint', 'lawn'
    ]
    
    def __init__(self, config):
        super().__init__(config)
    
    def get_product_price(self, product_id: str) -> Optional[float]:
        """Get current price for a product using product ID"""
        try:
            soup = self._get_soup(f"{self.BASE_URL}/p/{product_id}")
            return self._select_price(soup, self.PRICE_SELECTORS)
        except Exception as e:
            print(f"Error fetching Home Depot price for {product_id}: {e}")
        return None
    
    def get_product_info(self, product_id: str) -> Dict:
        """Get detailed product information"""
        try:
            url = f"{self.BASE_URL}/p/{product_id}"
            soup = self._get_soup(url)
            
            return {
                'name': self._select_text(soup, 'h1.product-title', "Unknown"),
                'url': url,
                'category': self._select_breadcrumb_category(soup, '.breadcrumb a'),
                'price': self.get_product_price(product_id),
                'description': ''
            }
            
        except Exception as e:
            print(f"Error fetching Home Depot product info for {product_id}: {e}")
        return {}
    
    def search_products(self, query: str, category: str = None) -> List[Dict]:
        """Search for products on Home Depot"""
        try:
            params = {
                'NCNI-5': '1',
                'Nao-': '1',
                'Ns': None,  # Sort parameter
                'M': None    # Category filter
            }
            
            if category:
                params['M'] = category
            
            soup = self._get_soup(f"{self.BASE_URL}/s/{query}", params=params)
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
                    if '/p/' not in product_url:
                        continue
                    product_id = product_url.split('/p/')[-1].split('/')[0]
                    
                    products.append(build_product_record(
                        product_id=product_id,
                        name=self._select_text(card, '.product-pod__title', "Unknown"),
                        url=f"{self.BASE_URL}{product_url}",
                        category=category,
                        price=parse_price(self._select_text(card, '.price__format')),
                        retailer='homedepot'
                    ))
                    
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
        return self.search_products(pick_search_term(category, self.POPULAR_SEARCHES), category)
