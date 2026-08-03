from typing import Dict, Optional, List
import requests
from .base import BaseScraper, validate_domain

class ShopScoutScraper(BaseScraper):
    """ShopScout scraper for Shopify stores - no API key required"""
    
    # Using the public ShopScout API approach
    BASE_URL = "https://api.shopscout.io/v1"
    
    def __init__(self, config):
        super().__init__(config)
    
    def get_store_products(self, domain: str) -> List[Dict]:
        """Get all products from a Shopify store"""
        try:
            # Shopify stores have a public JSON API at /products.json
            url = f"https://{validate_domain(domain)}/products.json"
            
            response = requests.get(url, headers=self._get_headers(), timeout=self.REQUEST_TIMEOUT)
            response.raise_for_status()
            
            data = response.json()
            products = []
            
            for product in data.get('products', []):
                # Get the first available variant price
                price = None
                for variant in product.get('variants', []):
                    if variant.get('available'):
                        price = float(variant.get('price', 0))
                        break
                
                if not price and product.get('variants'):
                    # Fallback to first variant price
                    price = float(product['variants'][0].get('price', 0))
                
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
            
        except Exception as e:
            print(f"Error scraping Shopify store {domain}: {e}")
            return []
    
    def get_product_price(self, product_id: str, domain: str) -> Optional[float]:
        """Get current price for a specific product from a Shopify store"""
        try:
            url = f"https://{validate_domain(domain)}/products.json"
            response = requests.get(url, headers=self._get_headers(), timeout=self.REQUEST_TIMEOUT)
            response.raise_for_status()
            
            data = response.json()
            
            for product in data.get('products', []):
                if str(product.get('id')) == product_id:
                    # Get first available variant price
                    for variant in product.get('variants', []):
                        if variant.get('available'):
                            return float(variant.get('price', 0))
                    
                    # Fallback to first variant
                    if product.get('variants'):
                        return float(product['variants'][0].get('price', 0))
            
            return None
            
        except Exception as e:
            print(f"Error fetching price for product {product_id} from {domain}: {e}")
            return None
    
    def get_product_info(self, product_id: str, domain: str) -> Dict:
        """Get detailed product information from a Shopify store"""
        try:
            url = f"https://{validate_domain(domain)}/products.json"
            response = requests.get(url, headers=self._get_headers(), timeout=self.REQUEST_TIMEOUT)
            response.raise_for_status()
            
            data = response.json()
            
            for product in data.get('products', []):
                if str(product.get('id')) == product_id:
                    price = None
                    for variant in product.get('variants', []):
                        if variant.get('available'):
                            price = float(variant.get('price', 0))
                            break
                    
                    if not price and product.get('variants'):
                        price = float(product['variants'][0].get('price', 0))
                    
                    return {
                        'name': product.get('title'),
                        'url': f"https://{domain}/products/{product.get('handle')}",
                        'category': 'Unknown',
                        'price': price,
                        'description': product.get('body_html', ''),
                        'images': [img.get('src') for img in product.get('images', [])],
                        'vendor': product.get('vendor'),
                        'product_type': product.get('product_type'),
                        'tags': product.get('tags', '')
                    }
            
            return {}
            
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