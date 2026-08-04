"""
BuyWhere API Scraper - Real products from Amazon, Best Buy, Walmart
"""

import requests
from typing import Dict, Optional, List
from .base import BaseScraper

class BuyWhereScraper(BaseScraper):
    """BuyWhere API scraper for real product data"""
    
    def __init__(self, config):
        super().__init__(config)
        self.api_key = config.BUYWHERE_API_KEY
        self.base_url = "https://api.buywhere.ai/v1"
        self.headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }
    
    def search_products(self, query: str, category: str = None, limit: int = 20) -> List[Dict]:
        """Search for products using BuyWhere API"""
        if not self.api_key:
            print("BuyWhere API key not configured")
            return []
        
        try:
            params = {
                'q': query,
                'country_code': 'US',
                'limit': limit
            }
            
            response = requests.get(
                f"{self.base_url}/products/search",
                headers=self.headers,
                params=params,
                timeout=10
            )
            
            print(f"API Response Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                # Don't print full response to avoid encoding issues
                print(f"API Response received, meta: {data.get('meta', {})}")
                
                products = []
                
                # Handle different response formats
                if 'products' in data:
                    items = data['products']
                elif 'data' in data:
                    items = data['data']
                elif isinstance(data, list):
                    items = data
                else:
                    print(f"Unexpected response format: {data}")
                    return []
                
                for item in items:
                    # Handle different field names
                    product_id = item.get('id') or item.get('product_id') or str(hash(item.get('name', '')))
                    name = item.get('name') or item.get('title') or item.get('product_name', '')
                    url = item.get('url') or item.get('product_url', '')
                    price = item.get('price') or item.get('current_price') or item.get('price_usd', 0)
                    retailer = item.get('merchant') or item.get('retailer') or item.get('store', 'Unknown')
                    
                    # Handle price object
                    if isinstance(price, dict):
                        price = price.get('current') or price.get('amount') or price.get('value', 0)
                        # Convert SGD to USD if needed (approximate rate: 1 SGD = 0.74 USD)
                        currency = item.get('price', {}).get('currency', 'USD')
                        if currency == 'SGD':
                            price = float(price) * 0.74  # Convert to USD
                    
                    products.append({
                        'product_id': f"buywhere_{product_id}",
                        'name': name,
                        'url': url,
                        'category': item.get('category', category or 'General'),
                        'price': float(price) if price else 0,
                        'retailer': retailer,
                        'image': item.get('image_url', item.get('image', '')),
                        'availability': item.get('availability', 'unknown')
                    })
                
                print(f"Parsed {len(products)} products")
                return products
            else:
                print(f"BuyWhere API error: {response.status_code}")
                print(f"Response: {response.text}")
                return []
                
        except Exception as e:
            print(f"BuyWhere API error: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    def get_product_price(self, product_id: str) -> Optional[float]:
        """Get current price for a specific product"""
        if not self.api_key or not product_id.startswith('buywhere_'):
            return None
        
        try:
            # Extract the real product ID
            real_id = product_id.replace('buywhere_', '')
            
            response = requests.get(
                f"{self.base_url}/products/{real_id}",
                headers=self.headers,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                return data.get('price', {}).get('current', 0)
            else:
                return None
                
        except Exception as e:
            print(f"BuyWhere price error: {e}")
            return None
    
    def get_trending_products(self, category: str = 'all', limit: int = 20) -> List[Dict]:
        """Get trending products from BuyWhere"""
        # Use popular search terms for trending products
        trending_queries = [
            'wireless earbuds',
            'laptop stand',
            'usb-c hub',
            'bluetooth speaker',
            'phone charger',
            'led light bulbs',
            'kitchen utensils',
            'tool set',
            'storage containers',
            'pillows'
        ]
        
        all_products = []
        for query in trending_queries[:limit]:  # Limit number of queries
            products = self.search_products(query, category, limit=2)
            all_products.extend(products)
        
        return all_products[:limit]
    
    def get_product_info(self, product_id: str) -> Dict:
        """Get detailed product information"""
        if not self.api_key or not product_id.startswith('buywhere_'):
            return {}
        
        try:
            real_id = product_id.replace('buywhere_', '')
            
            response = requests.get(
                f"{self.base_url}/products/{real_id}",
                headers=self.headers,
                timeout=10
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                return {}
                
        except Exception as e:
            print(f"BuyWhere product info error: {e}")
            return {}
