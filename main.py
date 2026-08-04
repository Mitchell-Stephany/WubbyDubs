import asyncio
import time
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from datetime import datetime
import threading

from config import Config
from database import Database
from scrapers.browser_scraper import BrowserScraper
from ebay_api import eBayAPI
from discord_bot import DiscordBot
from price_analyzer import PriceAnalyzer
from search_terms import get_random_search_terms, get_all_terms

class PriceTracker:
    """Main price tracking system using browser-based scraping"""
    
    def __init__(self):
        print("Loading configuration...")
        self.config = Config()
        print("Configuration loaded")
        
        print("Initializing database...")
        self.db = Database()
        print("Database initialized")
        
        # Initialize browser scraper (Playwright with stealth)
        print("Initializing browser scraper (Playwright)...")
        self.browser_scraper = BrowserScraper(self.config, headless=True)
        print("Browser scraper initialized")
        
        # Initialize eBay API
        print("Initializing eBay API...")
        self.ebay_api = eBayAPI(self.config)
        print(f"eBay API initialized (enabled: {self.ebay_api.enabled})")
        
        # Initialize components
        print("Initializing price analyzer...")
        self.price_analyzer = PriceAnalyzer(self.config, self.db, self.ebay_api, self.browser_scraper)
        print("Price analyzer initialized (with eBay arbitrage calculation)")
        
        # Discord bot (will be started in separate thread)
        print("Initializing Discord bot...")
        self.discord_bot = DiscordBot(self.config)
        self.discord_thread = None
        print("Discord bot initialized")
        
        # Track recently searched terms to avoid repetition
        self.recent_searches = set()
        
        # Scheduler
        print("Initializing scheduler...")
        self.scheduler = AsyncIOScheduler()
        print("Scheduler initialized")
        
        print("PriceTracker initialization complete")
        print(f"  Search pool: {len(get_all_terms())} product terms across 7 categories")
    
    def start_discord_bot(self):
        """Start Discord bot in a separate thread"""
        def run_bot():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(self.discord_bot.start_bot())
        
        self.discord_thread = threading.Thread(target=run_bot, daemon=True)
        self.discord_thread.start()
        time.sleep(5)
    
    async def discover_products(self, queries: list = None):
        """Discover and add real products using browser scraper.
        
        Picks random search terms from a pool of 100+ product categories
        to avoid searching the same things every cycle.
        """
        # Get random search terms if not specified
        if queries is None:
            selected = get_random_search_terms(count=5, exclude=self.recent_searches)
            queries = [(term, category) for term, category in selected]
            
            # Track what we searched so we don't repeat next cycle
            for term, _ in queries:
                self.recent_searches.add(term)
            
            # Reset recent searches if we've used most of the pool
            if len(self.recent_searches) > len(get_all_terms()) * 0.7:
                self.recent_searches = set()
        
        print(f"\n[{datetime.now()}] Discovering products from {len(queries)} search queries...")
        print(f"  Search terms: {[q[0] if isinstance(q, tuple) else q for q in queries]}")
        
        try:
            await self.browser_scraper._start()
            total_added = 0
            
            for query_item in queries:
                if isinstance(query_item, tuple):
                    query, category = query_item
                else:
                    query, category = query_item, 'General'
                
                print(f"\n  Searching for '{query}' ({category})...")
                try:
                    products = await self.browser_scraper.search_all_retailers(query, limit_per_retailer=3)
                    
                    for product in products:
                        if product['price'] > 0 and product['url']:
                            self.db.add_product(
                                product_id=product['product_id'],
                                retailer=product['retailer'],
                                name=product['name'],
                                url=product['url'],
                                category=category
                            )
                            # Record initial price
                            self.db.update_price(product['product_id'], product['price'])
                            total_added += 1
                            print(f"    Added: {product['name'][:50]} - ${product['price']:.2f} ({product['retailer']})")
                
                except Exception as e:
                    print(f"    Error searching for '{query}': {e}")
                
                # Delay between searches to avoid rate limiting
                await asyncio.sleep(5)
            
            print(f"\n  Total products added: {total_added}")
            return total_added
            
        except Exception as e:
            print(f"  Discovery error: {e}")
            return 0
    
    async def check_prices(self):
        """Check prices for all tracked products by visiting product pages directly.
        
        Much more efficient than searching - 1 page load per product.
        """
        print(f"\n[{datetime.now()}] Starting price check...")
        
        products = self.db.get_all_products()
        print(f"Checking {len(products)} products...")
        
        if not products:
            print("No products to check. Run discovery first.")
            return
        
        try:
            await self.browser_scraper._start()
            
            updated = 0
            for product in products:
                retailer = product['retailer']
                url = product['url']
                product_id = product['product_id']
                
                # Skip retailers we can't scrape
                retailer_lower = retailer.lower()
                if not any(r in retailer_lower for r in ['amazon', 'walmart', 'target']):
                    continue
                
                try:
                    # Visit the product page directly and get the price
                    current_price = await self.browser_scraper.get_product_price(url, retailer)
                    
                    if current_price and current_price > 0:
                        self.db.update_price(product_id, current_price)
                        updated += 1
                        print(f"    [{retailer}] {product['name'][:40]} - ${current_price:.2f}")
                    else:
                        print(f"    [{retailer}] {product['name'][:40]} - no price found")
                    
                    # Rate limiting between products
                    await asyncio.sleep(5)
                    
                except Exception as e:
                    print(f"    Error checking {product['name'][:40]}: {e}")
                    await asyncio.sleep(3)
            
            print(f"\n  Price check complete: {updated}/{len(products)} prices updated")
            
        except Exception as e:
            print(f"  Price check error: {e}")
    
    async def analyze_and_notify(self):
        """Analyze price changes with eBay arbitrage calculation and send notifications"""
        print(f"\n[{datetime.now()}] Analyzing price changes with eBay arbitrage...")
        
        # Use async analysis that scrapes eBay sold listings
        deals = await self.price_analyzer.analyze_all_products_with_ebay()
        
        if deals:
            print(f"Found {len(deals)} deals!")
            
            # Sort by profit (most profitable first)
            deals.sort(key=lambda d: d.get('potential_profit', 0), reverse=True)
            
            await self.discord_bot.wait_until_ready()
            
            for deal in deals:
                try:
                    await self.discord_bot.send_deal_notification(deal)
                    await asyncio.sleep(1)
                except Exception as e:
                    print(f"Error sending notification: {e}")
        else:
            print("No profitable deals found")
    
    def setup_scheduler(self):
        """Setup the scheduled tasks"""
        # Discover products every 2 hours
        self.scheduler.add_job(
            self.discover_products,
            'interval',
            hours=2,
            id='discover_products',
            next_run_time=datetime.now()  # Run immediately on startup
        )
        
        # Check prices every 30 minutes
        self.scheduler.add_job(
            self.check_prices,
            'interval',
            minutes=30,
            id='check_prices'
        )
        
        # Analyze and notify every 30 minutes
        self.scheduler.add_job(
            self.analyze_and_notify,
            'interval',
            minutes=30,
            id='analyze_notify'
        )
    
    async def run(self):
        """Main run loop"""
        print("Starting Price Arbitrage Tracker...")
        print("  Retailers: Amazon, Walmart, Target")
        print("  Note: Home Depot and Lowe's are blocked by anti-bot measures")
        
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
        
        # Keep running
        try:
            while True:
                await asyncio.sleep(60)
        except KeyboardInterrupt:
            print("Shutting down...")
            self.scheduler.shutdown()
            await self.browser_scraper.close()
            
            if self.discord_thread and self.discord_thread.is_alive():
                loop = asyncio.get_event_loop()
                loop.run_until_complete(self.discord_bot.close())

def main():
    """Main entry point"""
    print("=" * 60)
    print("  Price Arbitrage Tracker - Browser-Based Scraping")
    print("  Uses Playwright with stealth mode for anti-bot bypass")
    print("=" * 60)
    
    print("\nInitializing Price Tracker...")
    tracker = PriceTracker()
    
    print("\nStarting async loop...")
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
