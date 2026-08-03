"""
Simple script that finds deals and sends Discord notifications
No complex async startup - just finds deals and notifies
"""

import time
import asyncio
from datetime import datetime
from config import Config
from database import Database
from scrapers.multi_source import MultiSourceScraper
from ebay_api import eBayAPI
from discord_bot import DiscordBot
from price_analyzer import PriceAnalyzer
from trend_discovery import TrendDiscovery

def main():
    """Main function - run this to check for deals and send Discord notifications"""
    print("=" * 50)
    print("Deal Finder with Discord Notifications")
    print("=" * 50)
    
    # Initialize components
    print("\n1. Initializing...")
    config = Config()
    db = Database()
    scraper = MultiSourceScraper(config)
    ebay_api = eBayAPI(config)
    price_analyzer = PriceAnalyzer(config, db, ebay_api)
    trend_discovery = TrendDiscovery(config, db)
    discord_bot = DiscordBot(config)
    print("   Components ready")
    
    # Discover products
    print("\n2. Finding products...")
    products = trend_discovery.discover_trending_products(max_products=10)
    print(f"   Found {len(products)} products")
    
    # Add to database
    print("\n3. Adding to database...")
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
        except:
            pass
    print("   Products added")
    
    # Simulate price changes (to create deals)
    print("\n4. Simulating price changes...")
    time.sleep(2)
    all_products = db.get_all_products()
    for product in all_products:
        new_price = scraper.get_product_price(product['product_id'])
        if new_price:
            db.update_price(product['product_id'], new_price)
    print("   Prices updated")
    
    # Find deals
    print("\n5. Finding deals...")
    deals = price_analyzer.analyze_all_products()
    
    if deals:
        print(f"   Found {len(deals)} deals!")
        
        # Send Discord notifications
        print("\n6. Sending Discord notifications...")
        try:
            # Simple async wrapper
            async def send_notifications():
                await discord_bot.start_bot()
                await discord_bot.wait_until_ready()
                
                for deal in deals:
                    deal_data = {
                        **deal,
                        'url': deal.get('url', products[0].get('url', 'https://example.com') if products else 'https://example.com'),
                        'retailer': deal.get('retailer', 'Multi-Source'),
                        'category': deal.get('category', 'General')
                    }
                    await discord_bot.send_deal_notification(deal_data)
                    print(f"   Sent: {deal['name']} ({deal['drop_percentage']:.1f}% drop)")
                    await asyncio.sleep(2)
                
                await discord_bot.close()
            
            # Run async function
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(send_notifications())
            loop.close()
            
            print("   All notifications sent")
            
        except Exception as e:
            print(f"   Discord error: {e}")
            print("   Displaying deals instead:")
            for deal in deals:
                print(f"   - {deal['name']}: {deal['drop_percentage']:.1f}% drop")
    else:
        print("   No deals found this time")
    
    print("\n" + "=" * 50)
    print(f"Completed at {datetime.now()}")
    print("=" * 50)
    print(f"\nTracking {len(db.get_all_products())} products")
    print("Run this script again to check for new deals")

if __name__ == "__main__":
    main()
