import logging
from typing import Dict, Optional, List
import requests
from exceptions import ConfigError, ScraperError
from .base import BaseScraper

logger = logging.getLogger(__name__)

class BestBuyScraper(BaseScraper):
    """Best Buy API scraper"""
    
    BASE_URL = "https://api.bestbuy.com/v1/products"
    
    def __init__(self, config):
        super().__init__(config)
        self.api_key = config.BEST_BUY_API_KEY
        if not self.api_key:
            raise ConfigError("BEST_BUY_API_KEY is required to use the Best Buy scraper")

    def _fetch(self, url: str, params: Dict) -> Dict:
        """Fetch and decode a Best Buy API response, raising ScraperError on failure."""
        try:
            response = self._get(url, params=params)
            return response.json()
        except requests.RequestException as exc:
            raise ScraperError(f"Best Buy request to {url} failed: {exc}") from exc
        except ValueError as exc:
            raise ScraperError(f"Best Buy returned a non-JSON response from {url}: {exc}") from exc

    @staticmethod
    def _first_product(data) -> Optional[Dict]:
        """Normalise the single-product endpoint, which may return an object or a list."""
        if isinstance(data, dict):
            products = data.get('products')
            if products:
                return products[0]
            return data or None
        if isinstance(data, list) and data:
            return data[0]
        return None

    def get_product_price(self, product_id: str) -> Optional[float]:
        """Get current price for a product using SKU"""
        url = f"{self.BASE_URL}/{product_id}.json"
        params = {
            'apiKey': self.api_key,
            'show': 'salePrice,regularPrice,name,url'
        }

        product = self._first_product(self._fetch(url, params))
        if not product:
            logger.warning("Best Buy returned no data for SKU %s", product_id)
            return None

        price = product.get('salePrice') or product.get('regularPrice')
        if price is None:
            logger.warning("Best Buy listing for SKU %s has no price", product_id)
            return None
        try:
            return float(price)
        except (TypeError, ValueError) as exc:
            raise ScraperError(
                f"Best Buy returned an unparseable price {price!r} for SKU {product_id}"
            ) from exc

    def get_product_info(self, product_id: str) -> Dict:
        """Get detailed product information"""
        url = f"{self.BASE_URL}/{product_id}.json"
        params = {
            'apiKey': self.api_key,
            'show': 'name,url,categoryPath,salePrice,regularPrice,description,image'
        }

        product = self._first_product(self._fetch(url, params))
        if not product:
            logger.warning("Best Buy returned no product info for SKU %s", product_id)
            return {}

        return {
            'name': product.get('name'),
            'url': product.get('url'),
            'category': product.get('categoryPath', ['Unknown'])[0] if product.get('categoryPath') else 'Unknown',
            'price': product.get('salePrice') or product.get('regularPrice'),
            'regular_price': product.get('regularPrice'),
            'description': product.get('description'),
            'image': product.get('image')
        }

    def _to_products(self, data) -> List[Dict]:
        # Single-product endpoints return a list, search endpoints a {"products": [...]} object.
        if isinstance(data, dict):
            data = data.get('products', [])
        return [
            {
                'product_id': str(product.get('sku')),
                'name': product.get('name'),
                'url': product.get('url'),
                'category': product.get('categoryPath', ['Unknown'])[0] if product.get('categoryPath') else 'Unknown',
                'price': product.get('salePrice') or product.get('regularPrice'),
                'retailer': 'bestbuy'
            }
            for product in data
        ]

    def search_products(self, query: str, category: str = None) -> List[Dict]:
        """Search for products on Best Buy"""
        params = {
            'apiKey': self.api_key,
            'query': query,
            'show': 'sku,name,url,categoryPath,salePrice,regularPrice',
            'pageSize': 20,
            'sort': 'bestSelling.desc'
        }

        if category:
            params['categoryPath.id'] = category

        return self._to_products(self._fetch(self.BASE_URL, params))

    def get_trending_products(self, category: str = 'all') -> List[Dict]:
        """Get trending/best-selling products"""
        params = {
            'apiKey': self.api_key,
            'show': 'sku,name,url,categoryPath,salePrice,regularPrice',
            'pageSize': 50,
            'sort': 'bestSelling.desc'
        }

        if category != 'all':
            params['categoryPath.id'] = category

        return self._to_products(self._fetch(self.BASE_URL, params))
