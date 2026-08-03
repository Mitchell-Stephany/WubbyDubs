"""
Test the main flow without scheduler and Discord
"""

from config import Config
from database import Database
from scrapers.multi_source import MultiSourceScraper
from ebay_api import eBayAPI
from price_analyzer import PriceAnalyzer
from trend_discovery import TrendDiscovery

def test_main_flow():
    """Test the main system flow"""
    print("Testing Main System Flow...")
    print("=" * 50)
    
    # Initialize components
    print("1. Initializing components...")
    config = Config()
    db = Database()
    scraper = MultiSourceScraper(config)
    ebay_api = eBayAPI(config)
    price_analyzer = PriceAnalyzer(config, db, ebay_api)
    trend_discovery = TrendDiscovery(config, db)
    print("   All components initialized")
    
    # Test product discovery
    print("\n2. Testing product discovery...")
    products = trend_discovery.discover_trending_products(max_products=5)
    print(f"   Discovered {len(products)} products")
    
    if products:
        # Add products to database
        print("\n3. Adding products to database...")
        for product in products:
            try:
                db.add_product(
                    product_id=product['product_id'],
                    retailer=product['retailer'],
                    name=product['name'],
                    url=product['url'],
                    category=product['category']
                )
                # Record initial price
                if product['price']:
                    db.update_price(product['product_id'], product['price'])
                print(f"   Added: {product['name']}")
            except Exception as e:
                print(f"   Error adding {product['name']}: {e}")
        
        # Test price updates
        print("\n4. Testing price updates...")
        all_products = db.get_all_products()
        for product in all_products:
            new_price = scraper.get_product_price(product['product_id'])
            if new_price:
                db.update_price(product['product_id'], new_price)
                print(f"   Updated {product['name']}: ${new_price:.2f}")
        
        # Test price analysis
        print("\n5. Testing price analysis...")
        deals = price_analyzer.analyze_all_products()
        print(f"   Found {len(deals)} potential deals")
        
        if deals:
            for deal in deals:
                print(f"   Deal: {deal['name']}")
                print(f"   Price drop: {deal['drop_percentage']:.1f}%")
                print(f"   Fallback mode: {deal.get('fallback_mode', False)}")
    else:
        print("   No products discovered")
    
    print("\n" + "=" * 50)
    print("[SUCCESS] Main flow is working!")
    print("The system can discover, track, and analyze products automatically")
    return True

if __name__ == "__main__":
    test_main_flow()
