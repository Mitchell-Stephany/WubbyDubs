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
        
        # Initialize scrapers based on configuration
        self.scrapers = {
            'multi_source': MultiSourceScraper(config)
        }
        
        # Remove None values
        self.scrapers = {k: v for k, v in self.scrapers.items() if v is not None}
        
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
        
        for retailer in self.config.RETAILERS:
            if retailer not in self.scrapers:
                continue
            
            scraper = self.scrapers[retailer]
            
            # Get trending products from each category
            for category in self.config.CATEGORIES:
                try:
                    if hasattr(scraper, 'get_trending_products'):
                        products = scraper.get_trending_products(category, limit=10)
                    else:
                        # Fallback to search if get_trending_products not available
                        search_term = self._get_random_search_term(category)
                        products = scraper.search_products(search_term, category, limit=10)
                    
                    all_products.extend(products)
                    
                    # Add delay between categories to avoid detection
                    if self.config.ADVANCED_SCRAPING:
                        import time
                        time.sleep(random.uniform(2, 4))
                    
                except Exception as e:
                    print(f"Error discovering products from {retailer} in {category}: {e}")
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
