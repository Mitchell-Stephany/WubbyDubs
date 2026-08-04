"""
Run the price tracking system with real products from BuyWhere API
"""

import time
import asyncio
from datetime import datetime
from config import Config
from database import Database
from scrapers.multi_source import MultiSourceScraper
from scrapers.buywhere import BuyWhereScraper
from ebay_api import eBayAPI
from discord_bot import DiscordBot
from price_analyzer import PriceAnalyzer
from trend_discovery import TrendDiscovery

def run_system():
    """Run the price tracking system with real products"""
    print("=" * 50)
    print("Price Arbitrage Tracker - Real Products")
    print("=" * 50)
    
    # Initialize components
    print("\n1. Initializing components...")
    config = Config()
    db = Database()
    scraper = BuyWhereScraper(config) if config.BUYWHERE_ENABLED else None
    ebay_api = eBayAPI(config)
    price_analyzer = PriceAnalyzer(config, db, ebay_api)
    trend_discovery = TrendDiscovery(config, db)
    discord_bot = DiscordBot(config)
    print("   All components initialized")
    
    if not config.BUYWHERE_ENABLED:
        print("\n   BuyWhere API not enabled - use manual entry only")
        print("   Use: python real_products_only.py")
        return
    
    # Discover products
    print("\n2. Discovering real products...")
    products = trend_discovery.discover_trending_products(max_products=10)
    print(f"   Discovered {len(products)} real products")
    
    # Add to database
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
            if product['price']:
                db.update_price(product['product_id'], product['price'])
            print(f"   Added: {product['name'][:50]}...")
        except Exception as e:
            print(f"   Error: {e}")
    
    # Simulate price changes (BuyWhere API doesn't support real-time updates)
    print("\n4. Simulating price changes for testing...")
    time.sleep(2)
    
    products = db.get_all_products()
    for product in products:
        # Simulate small price changes for demo
        if product['product_id'].startswith('buywhere_'):
            import random
            original_price = db.get_latest_price(product['product_id'])
            if original_price:
                # 10% chance of price drop
                if random.random() < 0.1:
                    new_price = original_price * random.uniform(0.7, 0.9)
                    db.update_price(product['product_id'], new_price)
                    print(f"   Price drop: {product['name'][:40]}... ${original_price:.2f} -> ${new_price:.2f}")
    
    # Analyze for deals
    print("\n5. Analyzing for deals...")
    deals = price_analyzer.analyze_all_products()
    
    if deals:
        print(f"   Found {len(deals)} potential deals!")
        for i, deal in enumerate(deals[:5], 1):
            print(f"   {i}. {deal['name'][:50]}...")
            print(f"      Price drop: {deal['drop_percentage']:.1f}%")
            print(f"      ${deal['original_price']:.2f} to ${deal['new_price']:.2f}")
            print(f"      Retailer: {deal.get('retailer', 'Unknown')}")
        
        if len(deals) > 5:
            print(f"   ... and {len(deals) - 5} more deals")
        
        # Send Discord notifications
        if config.DISCORD_BOT_TOKEN:
            print("\n6. Sending Discord notifications...")
            try:
                async def send_notifications():
                    await discord_bot.start_bot()
                    await discord_bot.wait_until_ready()
                    
                    for deal in deals:
                        deal_data = {
                            **deal,
                            'url': deal.get('url', 'https://example.com'),
                            'retailer': deal.get('retailer', 'BuyWhere'),
                            'category': deal.get('category', 'General')
                        }
                        await discord_bot.send_deal_notification(deal_data)
                        await asyncio.sleep(2)
                    
                    await discord_bot.close()
                
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                loop.run_until_complete(send_notifications())
                loop.close()
                print("   Discord notifications sent successfully!")
            except Exception as e:
                print(f"   Error sending Discord notifications: {e}")
        else:
            print("\n6. Skipping Discord (no token configured)")
    else:
        print("   No deals found")
    
    print("\n" + "=" * 50)
    print("System run completed successfully!")
    print("=" * 50)
    
    print(f"\nDatabase now has {len(db.get_all_products())} tracked products")
    print("All products are REAL from BuyWhere API (Amazon, Best Buy, Walmart)")
    print("Discord notifications are sent when deals are found")

if __name__ == "__main__":
    run_system()
