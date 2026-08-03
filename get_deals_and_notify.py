"""
Simple script: Get current deals and send Discord notifications
Run this whenever you want to check for deals
"""

import asyncio
from datetime import datetime
from config import Config
from database import Database
from scrapers.multi_source import MultiSourceScraper
from ebay_api import eBayAPI
from discord_bot import DiscordBot
from price_analyzer import PriceAnalyzer

async def check_and_notify():
    """Check for deals and send Discord notifications"""
    print("Checking for deals and sending Discord notifications...")
    print("=" * 50)
    
    config = Config()
    db = Database()
    scraper = MultiSourceScraper(config)
    ebay_api = eBayAPI(config)
    price_analyzer = PriceAnalyzer(config, db, ebay_api)
    discord_bot = DiscordBot(config)
    
    # Start Discord bot
    print("Starting Discord bot...")
    await discord_bot.start_bot()
    await discord_bot.wait_until_ready()
    print("Discord bot connected")
    
    try:
        # Update prices
        print("\nUpdating prices...")
        products = db.get_all_products()
        for product in products:
            new_price = scraper.get_product_price(product['product_id'])
            if new_price:
                db.update_price(product['product_id'], new_price)
                print(f"Updated: {product['name']}")
        
        # Check for deals
        print("\nAnalyzing for deals...")
        deals = price_analyzer.analyze_all_products()
        
        if deals:
            print(f"Found {len(deals)} deals!")
            
            # Send Discord notifications
            for deal in deals:
                deal_data = {
                    **deal,
                    'url': deal.get('url', 'https://example.com'),
                    'retailer': deal.get('retailer', 'Multi-Source'),
                    'category': deal.get('category', 'General')
                }
                await discord_bot.send_deal_notification(deal_data)
                print(f"Sent: {deal['name']} ({deal['drop_percentage']:.1f}% drop)")
                await asyncio.sleep(2)
        else:
            print("No deals found")
        
        print(f"\n[{datetime.now()}] Check completed")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await discord_bot.close()
        print("Discord bot closed")

def main():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(check_and_notify())
    finally:
        loop.close()

if __name__ == "__main__":
    main()
