import logging
from typing import Dict, Optional, List
import requests
from exceptions import ScraperError
from .base import BaseScraper

logger = logging.getLogger(__name__)

class ShopScoutScraper(BaseScraper):
    """ShopScout scraper for Shopify stores - no API key required"""
    
    # Using the public ShopScout API approach
    BASE_URL = "https://api.shopscout.io/v1"
    
    def __init__(self, config):
        super().__init__(config)

    def _fetch_catalog(self, domain: str) -> Dict:
        """Fetch a Shopify store catalog, raising ScraperError when it is unavailable."""
        # Shopify stores have a public JSON API at /products.json
        url = f"https://{domain}/products.json"
        try:
            return self._get(url).json()
        except requests.RequestException as exc:
            raise ScraperError(f"Shopify request to {url} failed: {exc}") from exc
        except ValueError as exc:
            raise ScraperError(f"Shopify store {domain} returned a non-JSON catalog: {exc}") from exc

    @staticmethod
    def _variant_price(product: Dict) -> Optional[float]:
        """Price of the first available variant, falling back to the first variant."""
        variants = product.get('variants', [])
        candidates = [v for v in variants if v.get('available')] or variants[:1]
        for variant in candidates:
            raw = variant.get('price')
            try:
                return float(raw)
            except (TypeError, ValueError):
                logger.warning(
                    "Ignoring unparseable Shopify variant price %r for product %s",
                    raw, product.get('id')
                )
        return None

    def get_store_products(self, domain: str) -> List[Dict]:
        """Get all products from a Shopify store"""
        data = self._fetch_catalog(domain)
        products = []

        for product in data.get('products', []):
            price = self._variant_price(product)

            products.append({
                'product_id': str(product.get('id')),
                'name': product.get('title'),
                'url': f"https://{domain}/products/{product.get('handle')}",
                'category': 'Unknown',  # Shopify doesn't always expose categories
                'price': price,
                'retailer': f'shopify_{domain}',
                'domain': domain,
                'description': product.get('body_html', ''),
                'images': [img.get('src') for img in product.get('images', [])]
            })

        return products

    def get_product_price(self, product_id: str, domain: str) -> Optional[float]:
        """Get current price for a specific product from a Shopify store"""
        data = self._fetch_catalog(domain)

        for product in data.get('products', []):
            if str(product.get('id')) == product_id:
                return self._variant_price(product)

        logger.warning("Product %s not found in Shopify catalog for %s", product_id, domain)
        return None

    def get_product_info(self, product_id: str, domain: str) -> Dict:
        """Get detailed product information from a Shopify store"""
        data = self._fetch_catalog(domain)

        for product in data.get('products', []):
            if str(product.get('id')) == product_id:
                return {
                    'name': product.get('title'),
                    'url': f"https://{domain}/products/{product.get('handle')}",
                    'category': 'Unknown',
                    'price': self._variant_price(product),
                    'description': product.get('body_html', ''),
                    'images': [img.get('src') for img in product.get('images', [])],
                    'vendor': product.get('vendor'),
                    'product_type': product.get('product_type'),
                    'tags': product.get('tags', '')
                }

        logger.warning("Product %s not found in Shopify catalog for %s", product_id, domain)
        return {}
    
    def search_products(self, query: str, domain: str = None) -> List[Dict]:
        """Search for products (Shopify doesn't have built-in search, returns all products)"""
        if domain:
            return self.get_store_products(domain)
        return []
    
    def get_trending_products(self, domain: str = None) -> List[Dict]:
        """Get products from a Shopify store (no trending endpoint, returns all)"""
        if domain:
            return self.get_store_products(domain)
        return []
    
    def get_popular_shopify_stores(self) -> List[str]:
        """Return list of popular Shopify stores to monitor"""
        # List of popular Shopify stores across different categories
        return [
            'gymshark.com',           # Fitness apparel
            'allbirds.com',           # Footwear
            'kyliecosmetics.com',     # Beauty
            'jeffreystarcosmetics.com', # Beauty
            'fashionnova.com',        # Fashion
            'ugmonk.com',             # Accessories
            'dbrand.com',             # Tech accessories
            'muskolife.com',          # Fitness
            'raoptics.com',           # Eyewear
            'mvmt.com',               # Watches
        ]