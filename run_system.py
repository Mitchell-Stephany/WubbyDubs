"""
Run the price tracking system without Discord complexity
"""

import logging
import sys
import time

from config import Config
from database import Database
from ebay_api import eBayAPI
from exceptions import DatabaseError, PriceTrackerError
from logging_config import configure_logging
from price_analyzer import PriceAnalyzer
from scrapers.multi_source import MultiSourceScraper
from trend_discovery import TrendDiscovery

logger = logging.getLogger(__name__)

def run_system():
    """Run the price tracking system"""
    print("=" * 50)
    print("Price Arbitrage Tracker - System Run")
    print("=" * 50)
    
    # Initialize components
    print("\n1. Initializing components...")
    config = Config()
    db = Database()
    scraper = MultiSourceScraper(config)
    ebay_api = eBayAPI(config)
    price_analyzer = PriceAnalyzer(config, db, ebay_api)
    trend_discovery = TrendDiscovery(config, db)
    print("   All components initialized")
    
    # Discover products
    print("\n2. Discovering products...")
    products = trend_discovery.discover_trending_products(max_products=10)
    print(f"   Discovered {len(products)} products")
    
    # Add to database
    print("\n3. Adding products to database...")
    failures = 0
    for product in products:
        try:
            db.add_product(
                product_id=product['product_id'],
                retailer=product['retailer'],
                name=product['name'],
                url=product['url'],
                category=product['category']
            )
            if product['price']:
                db.update_price(product['product_id'], product['price'])
            print(f"   Added: {product['name']}")
        except (DatabaseError, KeyError):
            logger.exception("Could not add product %r", product.get('name'))
            failures += 1

    if failures:
        raise DatabaseError(f"Failed to add {failures} of {len(products)} discovered products")
    
    # Simulate price changes
    print("\n4. Simulating price changes...")
    time.sleep(2)  # Wait for some time variance
    
    products = db.get_all_products()
    for product in products:
        new_price = scraper.get_product_price(product['product_id'])
        if new_price:
            db.update_price(product['product_id'], new_price)
            print(f"   Updated {product['name']}: ${new_price:.2f}")
    
    # Analyze for deals
    print("\n5. Analyzing for deals...")
    deals = price_analyzer.analyze_all_products()
    
    if deals:
        print(f"   Found {len(deals)} potential deals!")
        for i, deal in enumerate(deals[:5], 1):  # Show first 5 deals
            print(f"   {i}. {deal['name']}")
            print(f"      Price drop: {deal['drop_percentage']:.1f}%")
            print(f"      ${deal['original_price']:.2f} -> ${deal['new_price']:.2f}")
            print(f"      Fallback mode: {deal.get('fallback_mode', False)}")
        
        if len(deals) > 5:
            print(f"   ... and {len(deals) - 5} more deals")
    else:
        print("   No deals found")
    
    print("\n" + "=" * 50)
    print("System run completed successfully!")
    print("=" * 50)
    
    print(f"\nDatabase now has {len(db.get_all_products())} tracked products")
    print("Run this script again to see price changes over time")
    
    # Test Discord separately
    if config.DISCORD_BOT_TOKEN:
        print("\n" + "=" * 50)
        print("Testing Discord Integration")
        print("=" * 50)
        print("Run: python test_discord.py to test Discord separately")

if __name__ == "__main__":
    configure_logging()
    try:
        run_system()
    except PriceTrackerError:
        logger.exception("System run failed")
        sys.exit(1)
