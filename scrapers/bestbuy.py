from typing import Dict, Optional, List
import requests
from .base import BaseScraper, validate_product_id

class BestBuyScraper(BaseScraper):
    """Best Buy API scraper"""
    
    BASE_URL = "https://api.bestbuy.com/v1/products"
    
    def __init__(self, config):
        super().__init__(config)
        self.api_key = config.BEST_BUY_API_KEY
    
    def get_product_price(self, product_id: str) -> Optional[float]:
        """Get current price for a product using SKU"""
        try:
            url = f"{self.BASE_URL}/{validate_product_id(product_id)}.json"
            params = {
                'apiKey': self.api_key,
                'show': 'salePrice,regularPrice,name,url'
            }
            
            response = requests.get(url, params=params, headers=self._get_headers(), timeout=self.REQUEST_TIMEOUT)
            response.raise_for_status()
            
            data = response.json()
            if data and len(data) > 0:
                # Use sale price if available, otherwise regular price
                price = data[0].get('salePrice') or data[0].get('regularPrice')
                return float(price) if price else None
                
        except Exception as e:
            print(f"Error fetching Best Buy price for {product_id}: {e}")
        return None
    
    def get_product_info(self, product_id: str) -> Dict:
        """Get detailed product information"""
        try:
            url = f"{self.BASE_URL}/{validate_product_id(product_id)}.json"
            params = {
                'apiKey': self.api_key,
                'show': 'name,url,categoryPath,salePrice,regularPrice,description,image'
            }
            
            response = requests.get(url, params=params, headers=self._get_headers(), timeout=self.REQUEST_TIMEOUT)
            response.raise_for_status()
            
            data = response.json()
            if data and len(data) > 0:
                product = data[0]
                return {
                    'name': product.get('name'),
                    'url': product.get('url'),
                    'category': product.get('categoryPath', ['Unknown'])[0] if product.get('categoryPath') else 'Unknown',
                    'price': product.get('salePrice') or product.get('regularPrice'),
                    'regular_price': product.get('regularPrice'),
                    'description': product.get('description'),
                    'image': product.get('image')
                }
        except Exception as e:
            print(f"Error fetching Best Buy product info for {product_id}: {e}")
        return {}
    
    def search_products(self, query: str, category: str = None) -> List[Dict]:
        """Search for products on Best Buy"""
        try:
            url = self.BASE_URL
            params = {
                'apiKey': self.api_key,
                'query': query,
                'show': 'sku,name,url,categoryPath,salePrice,regularPrice',
                'pageSize': 20,
                'sort': 'bestSelling.desc'
            }
            
            if category:
                params['categoryPath.id'] = category
            
            response = requests.get(url, params=params, headers=self._get_headers(), timeout=self.REQUEST_TIMEOUT)
            response.raise_for_status()
            
            data = response.json()
            products = []
            
            for product in data:
                products.append({
                    'product_id': str(product.get('sku')),
                    'name': product.get('name'),
                    'url': product.get('url'),
                    'category': product.get('categoryPath', ['Unknown'])[0] if product.get('categoryPath') else 'Unknown',
                    'price': product.get('salePrice') or product.get('regularPrice'),
                    'retailer': 'bestbuy'
                })
            
            return products
            
        except Exception as e:
            print(f"Error searching Best Buy products: {e}")
        return []
    
    def get_trending_products(self, category: str = 'all') -> List[Dict]:
        """Get trending/best-selling products"""
        try:
            url = self.BASE_URL
            params = {
                'apiKey': self.api_key,
                'show': 'sku,name,url,categoryPath,salePrice,regularPrice',
                'pageSize': 50,
                'sort': 'bestSelling.desc'
            }
            
            if category != 'all':
                params['categoryPath.id'] = category
            
            response = requests.get(url, params=params, headers=self._get_headers(), timeout=self.REQUEST_TIMEOUT)
            response.raise_for_status()
            
            data = response.json()
            products = []
            
            for product in data:
                products.append({
                    'product_id': str(product.get('sku')),
                    'name': product.get('name'),
                    'url': product.get('url'),
                    'category': product.get('categoryPath', ['Unknown'])[0] if product.get('categoryPath') else 'Unknown',
                    'price': product.get('salePrice') or product.get('regularPrice'),
                    'retailer': 'bestbuy'
                })
            
            return products
            
        except Exception as e:
            print(f"Error fetching trending Best Buy products: {e}")
        return []
