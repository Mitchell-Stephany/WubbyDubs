from typing import Dict, Optional, List
from .base import BaseScraper
from utils import build_product_record

class BestBuyScraper(BaseScraper):
    """Best Buy API scraper"""
    
    BASE_URL = "https://api.bestbuy.com/v1/products"
    
    LIST_FIELDS = 'sku,name,url,categoryPath,salePrice,regularPrice'
    
    def __init__(self, config):
        super().__init__(config)
        self.api_key = config.BEST_BUY_API_KEY
    
    def _api_params(self, **params) -> Dict:
        """Build query parameters including the API key"""
        return {'apiKey': self.api_key, **params}
    
    @staticmethod
    def _product_price(product: Dict) -> Optional[float]:
        """Use sale price if available, otherwise regular price"""
        return product.get('salePrice') or product.get('regularPrice')
    
    @staticmethod
    def _product_category(product: Dict) -> str:
        """First entry of the category path"""
        category_path = product.get('categoryPath')
        return category_path[0] if category_path else 'Unknown'
    
    def _to_product_record(self, product: Dict) -> Dict:
        """Convert an API product into the shared product record shape"""
        return build_product_record(
            product_id=str(product.get('sku')),
            name=product.get('name'),
            url=product.get('url'),
            category=self._product_category(product),
            price=self._product_price(product),
            retailer='bestbuy'
        )
    
    def _list_products(self, params: Dict, error_message: str) -> List[Dict]:
        """Fetch a list of products from the API"""
        try:
            return [self._to_product_record(p) for p in self._get_json(self.BASE_URL, params=params)]
        except Exception as e:
            print(f"{error_message}: {e}")
        return []
    
    def get_product_price(self, product_id: str) -> Optional[float]:
        """Get current price for a product using SKU"""
        try:
            url = f"{self.BASE_URL}/{product_id}.json"
            params = self._api_params(show='salePrice,regularPrice,name,url')
            
            data = self._get_json(url, params=params)
            if data and len(data) > 0:
                price = self._product_price(data[0])
                return float(price) if price else None
                
        except Exception as e:
            print(f"Error fetching Best Buy price for {product_id}: {e}")
        return None
    
    def get_product_info(self, product_id: str) -> Dict:
        """Get detailed product information"""
        try:
            url = f"{self.BASE_URL}/{product_id}.json"
            params = self._api_params(show='name,url,categoryPath,salePrice,regularPrice,description,image')
            
            data = self._get_json(url, params=params)
            if data and len(data) > 0:
                product = data[0]
                return {
                    'name': product.get('name'),
                    'url': product.get('url'),
                    'category': self._product_category(product),
                    'price': self._product_price(product),
                    'regular_price': product.get('regularPrice'),
                    'description': product.get('description'),
                    'image': product.get('image')
                }
        except Exception as e:
            print(f"Error fetching Best Buy product info for {product_id}: {e}")
        return {}
    
    def search_products(self, query: str, category: str = None) -> List[Dict]:
        """Search for products on Best Buy"""
        params = self._api_params(
            query=query,
            show=self.LIST_FIELDS,
            pageSize=20,
            sort='bestSelling.desc'
        )
        
        if category:
            params['categoryPath.id'] = category
        
        return self._list_products(params, "Error searching Best Buy products")
    
    def get_trending_products(self, category: str = 'all') -> List[Dict]:
        """Get trending/best-selling products"""
        params = self._api_params(
            show=self.LIST_FIELDS,
            pageSize=50,
            sort='bestSelling.desc'
        )
        
        if category != 'all':
            params['categoryPath.id'] = category
        
        return self._list_products(params, "Error fetching trending Best Buy products")
