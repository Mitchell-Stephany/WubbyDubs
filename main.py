import asyncio
import time
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from datetime import datetime
import threading

from config import Config
from database import Database
from scrapers import BestBuyScraper, TargetScraper, HomeDepotScraper
from ebay_api import eBayAPI
from discord_bot import DiscordBot
from price_analyzer import PriceAnalyzer
from trend_discovery import TrendDiscovery

class PriceTracker:
    """Main price tracking system"""
    
    def __init__(self):
        print("Loading configuration...")
        self.config = Config()
        print("Configuration loaded")
        
        print("Initializing database...")
        self.db = Database()
        print("Database initialized")
        
        # Initialize scrapers
        print("Initializing scrapers...")
        self.scrapers = {
            'bestbuy': BestBuyScraper(self.config) if self.config.BEST_BUY_ENABLED else None,
            'target': TargetScraper(self.config),
            'homedepot': HomeDepotScraper(self.config)
        }
        
        # Remove None values
        self.scrapers = {k: v for k, v in self.scrapers.items() if v is not None}
        print(f"Scrapers initialized: {list(self.scrapers.keys())}")
        
        # Initialize eBay API
        print("Initializing eBay API...")
        self.ebay_api = eBayAPI(self.config)
        print(f"eBay API initialized (enabled: {self.ebay_api.enabled})")
        
        # Initialize components
        print("Initializing price analyzer...")
        self.price_analyzer = PriceAnalyzer(self.config, self.db, self.ebay_api)
        print("Price analyzer initialized")
        
        print("Initializing trend discovery...")
        self.trend_discovery = TrendDiscovery(self.config, self.db)
        print("Trend discovery initialized")
        
        # Discord bot (will be started in separate thread)
        print("Initializing Discord bot...")
        self.discord_bot = DiscordBot(self.config)
        self.discord_thread = None
        print("Discord bot initialized")
        
        # Scheduler
        print("Initializing scheduler...")
        self.scheduler = AsyncIOScheduler()
        print("Scheduler initialized")
        
        print("PriceTracker initialization complete")
    
    def start_discord_bot(self):
        """Start Discord bot in a separate thread"""
        def run_bot():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(self.discord_bot.start_bot())
        
        self.discord_thread = threading.Thread(target=run_bot, daemon=True)
        self.discord_thread.start()
        
        # Wait for bot to be ready
        time.sleep(5)  # Give it time to connect
    
    async def check_prices(self):
        """Check prices for all tracked products"""
        print(f"\n[{datetime.now()}] Starting price check...")
        
        products = self.db.get_all_products()
        print(f"Checking {len(products)} products...")
        
        for product in products:
            retailer = product['retailer']
            product_id = product['product_id']
            
            if retailer not in self.scrapers:
                continue
            
            scraper = self.scrapers[retailer]
            
            try:
                current_price = scraper.get_product_price(product_id)
                
                if current_price:
                    self.db.update_price(product_id, current_price)
                    print(f"Updated price for {product['name']}: ${current_price:.2f}")
                else:
                    print(f"Could not fetch price for {product['name']}")
                    
            except Exception as e:
                print(f"Error checking price for {product['name']}: {e}")
        
        print("Price check completed")
    
    async def analyze_and_notify(self):
        """Analyze price changes and send notifications"""
        print(f"\n[{datetime.now()}] Analyzing price changes...")
        
        deals = self.price_analyzer.analyze_all_products()
        
        if deals:
            print(f"Found {len(deals)} profitable deals!")
            
            # Wait for Discord bot to be ready
            await self.discord_bot.wait_until_ready()
            
            for deal in deals:
                try:
                    await self.discord_bot.send_deal_notification(deal)
                    # Small delay to avoid rate limiting
                    await asyncio.sleep(1)
                except Exception as e:
                    print(f"Error sending notification: {e}")
        else:
            print("No new profitable deals found")
    
    async def discover_new_products(self):
        """Discover and add new trending products"""
        print(f"\n[{datetime.now()}] Discovering new products...")
        
        try:
            added = self.trend_discovery.refresh_product_pool(max_products=30)
            print(f"Added {added} new products to track")
            if added == 0:
                print("Note: Scrapers may be blocked by anti-bot measures")
                print("Consider using official APIs for reliable data access")
        except Exception as e:
            print(f"Error discovering new products: {e}")
            print("Note: This is expected if retailers have anti-scraping measures")
    
    def setup_scheduler(self):
        """Setup the scheduled tasks"""
        # Check prices every 5 minutes
        self.scheduler.add_job(
            self.check_prices,
            'interval',
            minutes=self.config.CHECK_INTERVAL_MINUTES,
            id='check_prices'
        )
        
        # Analyze and notify every 5 minutes (after price check)
        self.scheduler.add_job(
            self.analyze_and_notify,
            'interval',
            minutes=self.config.CHECK_INTERVAL_MINUTES,
            id='analyze_notify'
        )
        
        # Discover new products every hour
        self.scheduler.add_job(
            self.discover_new_products,
            'interval',
            hours=1,
            id='discover_products'
        )
        
        # Initial tasks
        self.scheduler.add_job(
            self.discover_new_products,
            'date',
            run_date=datetime.now(),
            id='initial_discovery'
        )
    
    async def run(self):
        """Main run loop"""
        print("Starting Price Arbitrage Tracker...")
        
        # Start Discord bot
        if self.config.DISCORD_BOT_TOKEN:
            print("Starting Discord bot...")
            self.start_discord_bot()
        else:
            print("No Discord token configured, skipping bot startup")
        
        # Setup scheduler
        self.setup_scheduler()
        
        # Start scheduler
        self.scheduler.start()
        print("Scheduler started")
        
        # Keep the bot running
        try:
            while True:
                await asyncio.sleep(60)
        except KeyboardInterrupt:
            print("Shutting down...")
            self.scheduler.shutdown()
            if self.discord_thread and self.discord_thread.is_alive():
                # Stop the Discord bot
                loop = asyncio.get_event_loop()
                loop.run_until_complete(self.discord_bot.close())

def main():
    """Main entry point"""
    print("Initializing Price Tracker...")
    tracker = PriceTracker()
    print("Price Tracker initialized successfully")
    
    # Run the async main function
    print("Starting async loop...")
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    try:
        print("Running tracker...")
        loop.run_until_complete(tracker.run())
    except KeyboardInterrupt:
        print("\nShutting down gracefully...")
    finally:
        loop.close()

if __name__ == "__main__":
    main()
