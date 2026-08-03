from typing import Dict, Optional, List
from .base import BaseScraper
from utils import build_product_record, pick_search_term

class ShopteraScraper(BaseScraper):
    """Shoptera scraper for European e-shops - no API key required"""
    
    BASE_URL = "https://shoptera.ai/api/v1"
    
    SEARCH_TIMEOUT = 15
    
    # Approximate conversion rates (in production, use a real currency API)
    USD_RATES = {
        'EUR': 1.1,
        'CZK': 0.045,
        'PLN': 0.25,
    }
    
    POPULAR_SEARCHES = [
        'electronics', 'smartphone', 'laptop', 'headphones',
        'kitchen', 'blender', 'coffee maker',
        'furniture', 'sofa', 'chair',
        'clothing', 'jacket', 'shoes'
    ]
    
    def __init__(self, config):
        super().__init__(config)
    
    def search_products(self, query: str, category: str = None, 
                       min_price: float = None, max_price: float = None,
                       limit: int = 20) -> List[Dict]:
        """Search for products across European e-shops"""
        try:
            params = {
                'q': query,
                'limit': limit,
                'fields': 'title,price,currency,product_url,image_url,brand,category,eshop_name,eshop_domain'
            }
            
            if category:
                params['category'] = category
            if min_price:
                params['min_price'] = min_price
            if max_price:
                params['max_price'] = max_price
            
            data = self._get_json(f"{self.BASE_URL}/search", params=params, timeout=self.SEARCH_TIMEOUT)
            products = []
            
            for item in data.get('results', []):
                price = item.get('price', 0)
                currency = item.get('currency', 'EUR')
                
                products.append(build_product_record(
                    product_id=item.get('product_url', '').split('/')[-1] or str(hash(item.get('title', ''))),
                    name=item.get('title', ''),
                    url=item.get('product_url', ''),
                    category=item.get('category', 'Unknown'),
                    price=self._to_usd(price, currency),
                    retailer=f"shoptera_{item.get('eshop_domain', 'unknown')}",
                    original_price=price,
                    original_currency=currency,
                    brand=item.get('brand', ''),
                    image=item.get('image_url', ''),
                    eshop_name=item.get('eshop_name', ''),
                    eshop_domain=item.get('eshop_domain', '')
                ))
            
            return products
            
        except Exception as e:
            print(f"Error searching Shoptera products: {e}")
            return []
    
    @classmethod
    def _to_usd(cls, price: float, currency: str) -> float:
        """Convert a price to an approximate USD amount"""
        return price * cls.USD_RATES.get(currency, 1)
    
    def get_product_price(self, product_id: str) -> Optional[float]:
        """Shoptera doesn't have individual product lookup, search needed"""
        # This would require searching by title and matching
        return None
    
    def get_product_info(self, product_id: str) -> Dict:
        """Shoptera doesn't have individual product lookup"""
        return {}
    
    def get_trending_products(self, category: str = None, limit: int = 20) -> List[Dict]:
        """Get trending products (using popular search terms)"""
        search_term = pick_search_term(category, self.POPULAR_SEARCHES)
        return self.search_products(search_term, category=category, limit=limit)
    
    def get_categories(self) -> List[str]:
        """Get available product categories"""
        return [
            'electronics', 'smartphones', 'laptops', 'tablets',
            'kitchen', 'appliances', 'cookware',
            'furniture', 'home_decor', 'lighting',
            'clothing', 'shoes', 'accessories',
            'sports', 'fitness', 'outdoor',
            'beauty', 'skincare', 'makeup',
            'toys', 'games', 'baby'
        ]