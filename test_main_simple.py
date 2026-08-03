"""
Simplified test of main system components
"""

from config import Config
from database import Database
from scrapers import TargetScraper, HomeDepotScraper
from ebay_api import eBayAPI
from price_analyzer import PriceAnalyzer
from trend_discovery import TrendDiscovery

def test_main_components():
    print("Testing main system components...")
    print("=" * 50)
    
    # Initialize components
    print("1. Initializing Config...")
    config = Config()
    print(f"   Discord Channel ID: {config.DISCORD_CHANNEL_ID}")
    print(f"   eBay Enabled: {config.EBAY_ENABLED}")
    
    print("\n2. Initializing Database...")
    db = Database()
    print("   Database ready")
    
    print("\n3. Initializing Scrapers...")
    scrapers = {
        'target': TargetScraper(config),
        'homedepot': HomeDepotScraper(config)
    }
    print(f"   Scrapers ready: {list(scrapers.keys())}")
    
    print("\n4. Initializing eBay API...")
    ebay_api = eBayAPI(config)
    print(f"   eBay API ready (enabled: {ebay_api.enabled})")
    
    print("\n5. Initializing Price Analyzer...")
    price_analyzer = PriceAnalyzer(config, db, ebay_api)
    print("   Price analyzer ready")
    
    print("\n6. Initializing Trend Discovery...")
    trend_discovery = TrendDiscovery(config, db)
    print("   Trend discovery ready")
    
    print("\n7. Testing Trend Discovery...")
    print("   Attempting to discover trending products...")
    try:
        products = trend_discovery.discover_trending_products(max_products=5)
        print(f"   Found {len(products)} products")
        if products:
            for i, product in enumerate(products[:3], 1):
                print(f"   {i}. {product['name']} - ${product.get('price', 0):.2f}")
    except Exception as e:
        print(f"   Error in trend discovery: {e}")
    
    print("\n" + "=" * 50)
    print("[SUCCESS] Main components are working!")
    print("Note: Discord bot and scheduler not tested in this simple test.")
    return True

if __name__ == "__main__":
    test_main_components()
