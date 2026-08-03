import logging
from typing import Dict, Optional, List
import requests
from exceptions import ScraperError
from .base import BaseScraper

logger = logging.getLogger(__name__)

# Approximate conversion rates used until a real FX source is wired in
USD_RATES = {'EUR': 1.1, 'CZK': 0.045, 'PLN': 0.25, 'USD': 1.0}

class ShopteraScraper(BaseScraper):
    """Shoptera scraper for European e-shops - no API key required"""
    
    BASE_URL = "https://shoptera.ai/api/v1"
    
    def __init__(self, config):
        super().__init__(config)
    
    def search_products(self, query: str, category: str = None, 
                       min_price: float = None, max_price: float = None,
                       limit: int = 20) -> List[Dict]:
        """Search for products across European e-shops"""
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

        url = f"{self.BASE_URL}/search"
        try:
            data = self._get(url, params=params).json()
        except requests.RequestException as exc:
            raise ScraperError(f"Shoptera request to {url} failed: {exc}") from exc
        except ValueError as exc:
            raise ScraperError(f"Shoptera returned a non-JSON response from {url}: {exc}") from exc

        products = []
        skipped = 0

        for item in data.get('results', []):
            currency = item.get('currency', 'EUR')
            try:
                price = float(item.get('price', 0))
            except (TypeError, ValueError):
                logger.warning(
                    "Skipping Shoptera item %r with unparseable price %r",
                    item.get('title'), item.get('price')
                )
                skipped += 1
                continue

            rate = USD_RATES.get(currency)
            if rate is None:
                logger.warning(
                    "Unknown Shoptera currency %s for %r; using the raw price",
                    currency, item.get('title')
                )
                rate = 1.0
            price_usd = price * rate

            products.append({
                'product_id': item.get('product_url', '').split('/')[-1] or str(hash(item.get('title', ''))),
                'name': item.get('title', ''),
                'url': item.get('product_url', ''),
                'category': item.get('category', 'Unknown'),
                'price': price_usd,
                'retailer': f"shoptera_{item.get('eshop_domain', 'unknown')}",
                'original_price': price,
                'original_currency': currency,
                'brand': item.get('brand', ''),
                'image': item.get('image_url', ''),
                'eshop_name': item.get('eshop_name', ''),
                'eshop_domain': item.get('eshop_domain', '')
            })

        if skipped:
            logger.warning("Skipped %s Shoptera results with invalid prices", skipped)

        return products
    
    def get_product_price(self, product_id: str) -> Optional[float]:
        """Shoptera doesn't have individual product lookup, search needed"""
        # This would require searching by title and matching
        return None
    
    def get_product_info(self, product_id: str) -> Dict:
        """Shoptera doesn't have individual product lookup"""
        return {}
    
    def get_trending_products(self, category: str = None, limit: int = 20) -> List[Dict]:
        """Get trending products (using popular search terms)"""
        popular_searches = [
            'electronics', 'smartphone', 'laptop', 'headphones',
            'kitchen', 'blender', 'coffee maker',
            'furniture', 'sofa', 'chair',
            'clothing', 'jacket', 'shoes'
        ]
        
        if category:
            search_term = category
        else:
            search_term = popular_searches[0]
        
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