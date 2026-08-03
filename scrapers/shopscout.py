from typing import Dict, Optional, List
from .base import BaseScraper
from utils import build_product_record

class ShopScoutScraper(BaseScraper):
    """ShopScout scraper for Shopify stores - no API key required"""
    
    # Using the public ShopScout API approach
    BASE_URL = "https://api.shopscout.io/v1"
    
    STORE_TIMEOUT = 10
    
    def __init__(self, config):
        super().__init__(config)
    
    def _fetch_store_catalog(self, domain: str) -> List[Dict]:
        """Fetch the raw catalog exposed by a Shopify store"""
        # Shopify stores have a public JSON API at /products.json
        data = self._get_json(f"https://{domain}/products.json", timeout=self.STORE_TIMEOUT)
        return data.get('products', [])
    
    @staticmethod
    def _variant_price(product: Dict) -> Optional[float]:
        """Price of the first available variant, falling back to the first variant"""
        variants = product.get('variants', [])
        
        for variant in variants:
            if variant.get('available'):
                return float(variant.get('price', 0))
        
        return float(variants[0].get('price', 0)) if variants else None
    
    @staticmethod
    def _product_url(domain: str, product: Dict) -> str:
        """Public URL of a Shopify product"""
        return f"https://{domain}/products/{product.get('handle')}"
    
    def _find_product(self, domain: str, product_id: str) -> Optional[Dict]:
        """Find a single product in a store catalog by ID"""
        for product in self._fetch_store_catalog(domain):
            if str(product.get('id')) == product_id:
                return product
        return None
    
    def get_store_products(self, domain: str) -> List[Dict]:
        """Get all products from a Shopify store"""
        try:
            return [
                build_product_record(
                    product_id=str(product.get('id')),
                    name=product.get('title'),
                    url=self._product_url(domain, product),
                    # Shopify doesn't always expose categories
                    category='Unknown',
                    price=self._variant_price(product),
                    retailer=f'shopify_{domain}',
                    domain=domain,
                    description=product.get('body_html', ''),
                    images=[img.get('src') for img in product.get('images', [])]
                )
                for product in self._fetch_store_catalog(domain)
            ]
            
        except Exception as e:
            print(f"Error scraping Shopify store {domain}: {e}")
            return []
    
    def get_product_price(self, product_id: str, domain: str) -> Optional[float]:
        """Get current price for a specific product from a Shopify store"""
        try:
            product = self._find_product(domain, product_id)
            return self._variant_price(product) if product else None
            
        except Exception as e:
            print(f"Error fetching price for product {product_id} from {domain}: {e}")
            return None
    
    def get_product_info(self, product_id: str, domain: str) -> Dict:
        """Get detailed product information from a Shopify store"""
        try:
            product = self._find_product(domain, product_id)
            if not product:
                return {}
            
            return {
                'name': product.get('title'),
                'url': self._product_url(domain, product),
                'category': 'Unknown',
                'price': self._variant_price(product),
                'description': product.get('body_html', ''),
                'images': [img.get('src') for img in product.get('images', [])],
                'vendor': product.get('vendor'),
                'product_type': product.get('product_type'),
                'tags': product.get('tags', '')
            }
            
        except Exception as e:
            print(f"Error fetching product info for {product_id} from {domain}: {e}")
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
