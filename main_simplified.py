"""
Simplified main system that focuses on core functionality
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

class SimplifiedPriceTracker:
    """Simplified price tracking system"""
    
    def __init__(self):
        print("Initializing Price Tracker...")
        self.config = Config()
        self.db = Database()
        self.scraper = MultiSourceScraper(self.config)
        self.ebay_api = eBayAPI(self.config)
        self.price_analyzer = PriceAnalyzer(self.config, self.db, self.ebay_api)
        self.trend_discovery = TrendDiscovery(self.config, self.db)
        self.discord_bot = DiscordBot(self.config)
        print("Price Tracker initialized")
    
    def check_and_notify(self):
        """Check prices and send notifications"""
        print(f"\n[{datetime.now()}] Starting price check...")
        
        # Check prices for all tracked products
        products = self.db.get_all_products()
        print(f"Checking {len(products)} products...")
        
        for product in products:
            try:
                current_price = self.scraper.get_product_price(product['product_id'])
                if current_price:
                    self.db.update_price(product['product_id'], current_price)
                    print(f"Updated price for {product['name']}: ${current_price:.2f}")
            except Exception as e:
                print(f"Error checking price for {product['name']}: {e}")
        
        # Analyze for deals
        print("Analyzing for deals...")
        deals = self.price_analyzer.analyze_all_products()
        
        if deals:
            print(f"Found {len(deals)} potential deals!")
            for deal in deals:
                print(f"  Deal: {deal['name']} - {deal['drop_percentage']:.1f}% drop")
                print(f"    Previous: ${deal['original_price']:.2f} → Current: ${deal['new_price']:.2f}")
        else:
            print("No new deals found")
    
    def discover_products(self):
        """Discover new products"""
        print(f"\n[{datetime.now()}] Discovering new products...")
        try:
            added = self.trend_discovery.refresh_product_pool(max_products=10)
            print(f"Added {added} new products to track")
        except Exception as e:
            print(f"Error discovering products: {e}")
    
    def run_once(self):
        """Run a single check cycle"""
        print("=" * 50)
        print("Single Check Cycle")
        print("=" * 50)
        
        # Discover products
        self.discover_products()
        
        # Check prices and notify
        self.check_and_notify()
        
        # Try Discord notification for deals
        products = self.db.get_all_products()
        if products:
            try:
                # Get latest prices and analyze
                for product in products:
                    current_price = self.scraper.get_product_price(product['product_id'])
                    if current_price:
                        self.db.update_price(product['product_id'], current_price)
                
                deals = self.price_analyzer.analyze_all_products()
                
                if deals and self.config.DISCORD_BOT_TOKEN:
                    print("\nSending Discord notifications...")
                    try:
                        loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(loop)
                        
                        # Start bot
                        bot_task = asyncio.create_task(self.discord_bot.start_bot())
                        loop.run_until_complete(self.discord_bot.wait_until_ready())
                        
                        # Send notifications
                        for deal in deals:
                            loop.run_until_complete(self.discord_bot.send_deal_notification(deal))
                            time.sleep(1)
                        
                        # Close bot
                        loop.run_until_complete(self.discord_bot.close())
                        loop.close()
                        print("Discord notifications sent")
                    except Exception as e:
                        print(f"Discord error: {e}")
            except Exception as e:
                print(f"Error in Discord notification: {e}")
        
        print("\n" + "=" * 50)
        print("Check cycle completed")
        print("=" * 50)
    
    def run_continuous(self, interval_minutes=5):
        """Run continuous monitoring"""
        print(f"Starting continuous monitoring (every {interval_minutes} minutes)...")
        print("Press Ctrl+C to stop")
        
        try:
            while True:
                self.run_once()
                print(f"\nWaiting {interval_minutes} minutes until next check...")
                time.sleep(interval_minutes * 60)
        except KeyboardInterrupt:
            print("\nStopping...")

def main():
    """Main entry point"""
    tracker = SimplifiedPriceTracker()
    
    print("\nChoose mode:")
    print("1. Single check (one-time)")
    print("2. Continuous monitoring")
    
    choice = input("Enter choice (1-2): ").strip()
    
    if choice == '1':
        tracker.run_once()
    elif choice == '2':
        interval = input("Check interval in minutes (default 5): ").strip()
        interval = int(interval) if interval else 5
        tracker.run_continuous(interval)
    else:
        print("Invalid choice")

if __name__ == "__main__":
    main()
