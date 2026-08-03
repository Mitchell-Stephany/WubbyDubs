"""
Simple monitoring script that sends Discord notifications
Run this continuously to monitor for deals and send notifications
"""

import asyncio
import time
from datetime import datetime
from config import Config
from database import Database
from scrapers.multi_source import MultiSourceScraper
from ebay_api import eBayAPI
from discord_bot import DiscordBot
from price_analyzer import PriceAnalyzer
from trend_discovery import TrendDiscovery

async def monitor_and_notify():
    """Monitor prices and send Discord notifications"""
    print("Starting Price Monitor with Discord Notifications")
    print("=" * 50)
    
    config = Config()
    db = Database()
    scraper = MultiSourceScraper(config)
    ebay_api = eBayAPI(config)
    price_analyzer = PriceAnalyzer(config, db, ebay_api)
    discord_bot = DiscordBot(config)
    trend_discovery = TrendDiscovery(config, db)
    
    # Start Discord bot
    print("Starting Discord bot...")
    bot_task = asyncio.create_task(discord_bot.start_bot())
    await discord_bot.wait_until_ready()
    print("Discord bot connected and ready")
    
    try:
        # Discover products first
        print("\nDiscovering products...")
        products = trend_discovery.discover_trending_products(max_products=10)
        print(f"Discovered {len(products)} products")
        
        # Add to database
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
        
        # Monitor loop
        print("\nStarting monitoring loop (Ctrl+C to stop)...")
        print("Checking for deals every 30 seconds...")
        
        while True:
            # Check prices
            products = db.get_all_products()
            for product in products:
                new_price = scraper.get_product_price(product['product_id'])
                if new_price:
                    db.update_price(product['product_id'], new_price)
            
            # Analyze for deals
            deals = price_analyzer.analyze_all_products()
            
            if deals:
                print(f"\n[{datetime.now()}] Found {len(deals)} deals!")
                
                # Send Discord notifications
                for deal in deals:
                    deal_data = {
                        **deal,
                        'url': deal.get('url', 'https://example.com'),
                        'retailer': deal.get('retailer', 'Multi-Source'),
                        'category': deal.get('category', 'General')
                    }
                    await discord_bot.send_deal_notification(deal_data)
                    print(f"Sent notification for: {deal['name']}")
                    await asyncio.sleep(2)  # Delay between notifications
            else:
                print(f"[{datetime.now()}] No new deals")
            
            await asyncio.sleep(30)  # Wait 30 seconds between checks
            
    except KeyboardInterrupt:
        print("\nStopping monitor...")
    finally:
        await discord_bot.close()
        print("Discord bot closed")

def main():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(monitor_and_notify())
    except KeyboardInterrupt:
        print("\nShutdown complete")
    finally:
        loop.close()

if __name__ == "__main__":
    main()
