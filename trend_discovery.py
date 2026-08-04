from typing import List, Dict
from scrapers import BestBuyScraper, TargetScraper, HomeDepotScraper
from scrapers.multi_source import MultiSourceScraper
from database import Database
import random

class TrendDiscovery:
    """Discovers trending products to track"""
    
    def __init__(self, config, database: Database):
        self.config = config
        self.db = database
        
        # DISABLED - No automatic fake product discovery
        self.scrapers = {}
        print("Automatic product discovery disabled - use manual entry only")
        
        # Popular search terms for different categories
        self.search_terms = {
            'electronics': [
                'iPhone', 'Samsung Galaxy', 'MacBook', 'PlayStation', 'Xbox',
                'Nintendo Switch', 'AirPods', 'laptop', 'tablet', 'TV',
                'camera', 'headphones', 'smart watch', 'gaming monitor'
            ],
            'home_goods': [
                'furniture', 'mattress', 'blender', 'coffee maker', 'vacuum',
                'air purifier', 'humidifier', 'dehumidifier', 'rugs', 'curtains'
            ],
            'appliances': [
                'refrigerator', 'dishwasher', 'washing machine', 'dryer',
                'microwave', 'oven', 'air conditioner', 'freezer'
            ],
            'tools': [
                'drill', 'saw', 'tool set', 'ladder', 'generator',
                'pressure washer', 'lawn mower', 'trimmer', 'welder'
            ]
        }
    
    def discover_trending_products(self, max_products: int = 50) -> List[Dict]:
        """Discover trending products across all retailers"""
        all_products = []
        
        # Use available scrapers
        for scraper_name, scraper in self.scrapers.items():
            try:
                print(f"Searching with {scraper_name}...")
                
                if hasattr(scraper, 'get_trending_products'):
                    products = scraper.get_trending_products(limit=max_products)
                else:
                    # Fallback to search with trending keywords
                    trending_keywords = ['wireless earbuds', 'usb-c hub', 'laptop stand', 'led lights', 'kitchen tools']
                    products = []
                    for keyword in trending_keywords:
                        found = scraper.search_products(keyword, limit=5)
                        products.extend(found)
                
                all_products.extend(products)
                print(f"Found {len(products)} products from {scraper_name}")
                
            except Exception as e:
                print(f"Error with {scraper_name}: {e}")
                continue
        
        # Remove duplicates and limit
        unique_products = self._deduplicate_products(all_products)
        
        # Shuffle and limit to max_products
        random.shuffle(unique_products)
        return unique_products[:max_products]
    
    def _get_random_search_term(self, category: str) -> str:
        """Get a random search term for a category"""
        terms = self.search_terms.get(category, ['popular'])
        return random.choice(terms)
    
    def _deduplicate_products(self, products: List[Dict]) -> List[Dict]:
        """Remove duplicate products based on name similarity"""
        seen = set()
        unique_products = []
        
        for product in products:
            # Create a simple key for deduplication
            name_lower = product.get('name', '').lower()
            retailer = product.get('retailer', '')
            
            # Simple dedup by name + retailer
            key = f"{name_lower}_{retailer}"
            
            if key not in seen:
                seen.add(key)
                unique_products.append(product)
        
        return unique_products
    
    def add_discovered_products(self, products: List[Dict]):
        """Add discovered products to the database"""
        added_count = 0
        
        for product in products:
            try:
                self.db.add_product(
                    product_id=product['product_id'],
                    retailer=product['retailer'],
                    name=product['name'],
                    url=product.get('url', ''),
                    category=product.get('category', 'Unknown')
                )
                added_count += 1
            except Exception as e:
                print(f"Error adding product {product.get('name')}: {e}")
                continue
        
        print(f"Added {added_count} new products to track")
        return added_count
    
    def refresh_product_pool(self, max_products: int = 50):
        """Discover and add new trending products"""
        print("Discovering trending products...")
        products = self.discover_trending_products(max_products)
        added = self.add_discovered_products(products)
        return added
