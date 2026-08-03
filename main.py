import asyncio
import logging
import sys
import threading
import time
from datetime import datetime

from apscheduler.events import EVENT_JOB_ERROR
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from config import Config
from database import Database
from discord_bot import DiscordBot
from ebay_api import eBayAPI
from exceptions import NotificationError, PriceTrackerError
from logging_config import configure_logging
from price_analyzer import PriceAnalyzer
from scrapers.multi_source import MultiSourceScraper
from trend_discovery import TrendDiscovery

logger = logging.getLogger(__name__)

class PriceTracker:
    """Main price tracking system"""
    
    def __init__(self):
        self.config = Config()
        self.db = Database()

        # Initialize scrapers
        logger.info("Using multi-source scraper for reliable product discovery")
        self.scrapers = {
            'multi_source': MultiSourceScraper(self.config)
        }

        self.ebay_api = eBayAPI(self.config)
        logger.info("eBay API initialized (enabled: %s)", self.ebay_api.enabled)

        self.price_analyzer = PriceAnalyzer(self.config, self.db, self.ebay_api)
        self.trend_discovery = TrendDiscovery(self.config, self.db)

        # Discord bot (will be started in separate thread)
        self.discord_bot = DiscordBot(self.config)
        self.discord_thread = None

        self.scheduler = AsyncIOScheduler()
        self.scheduler.add_listener(self._on_job_error, EVENT_JOB_ERROR)

        logger.info("PriceTracker initialization complete")

    @staticmethod
    def _on_job_error(event):
        """APScheduler swallows job exceptions by default; surface them with a traceback."""
        logger.error(
            "Scheduled job %s raised an exception", event.job_id,
            exc_info=event.exception
        )

    def start_discord_bot(self):
        """Start Discord bot in a separate thread"""
        def run_bot():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                loop.run_until_complete(self.discord_bot.start_bot())
            except Exception:
                # The thread would otherwise die silently, leaving notifications broken.
                logger.exception("Discord bot thread stopped with an error")
            finally:
                loop.close()
        
        self.discord_thread = threading.Thread(target=run_bot, daemon=True)
        self.discord_thread.start()
        
        # Wait for bot to be ready
        time.sleep(5)  # Give it time to connect
    
    async def check_prices(self):
        """Check prices for all tracked products"""
        logger.info("Starting price check...")
        
        products = self.db.get_all_products()
        logger.info("Checking %s products...", len(products))
        failures = 0
        
        for product in products:
            retailer = product['retailer']
            product_id = product['product_id']
            
            if retailer not in self.scrapers:
                logger.warning(
                    "No scraper for retailer %s (product %s)", retailer, product_id
                )
                continue
            
            scraper = self.scrapers[retailer]
            
            try:
                current_price = scraper.get_product_price(product_id)
                
                if current_price:
                    self.db.update_price(product_id, current_price)
                    logger.info("Updated price for %s: $%.2f", product['name'], current_price)
                else:
                    logger.warning("Could not fetch price for %s", product['name'])
                    
            except PriceTrackerError:
                logger.exception("Error checking price for %s", product['name'])
                failures += 1
        
        if failures:
            logger.error("Price check failed for %s of %s products", failures, len(products))
        logger.info("Price check completed")
    
    async def analyze_and_notify(self):
        """Analyze price changes and send notifications"""
        logger.info("Analyzing price changes...")
        
        deals = self.price_analyzer.analyze_all_products()
        
        if not deals:
            logger.info("No new profitable deals found")
            return

        logger.info("Found %s profitable deals!", len(deals))

        if not self.config.DISCORD_BOT_TOKEN:
            logger.warning("Discord is not configured; %s deals were not sent", len(deals))
            return

        # Wait for Discord bot to be ready; raises instead of hanging forever
        await self.discord_bot.wait_until_ready()

        failures = 0
        for deal in deals:
            try:
                await self.discord_bot.deliver_deal(deal)
                # Small delay to avoid rate limiting
                await asyncio.sleep(1)
            except NotificationError:
                logger.exception("Error sending notification for %s", deal.get('name'))
                failures += 1

        if failures:
            logger.error("Failed to deliver %s of %s deal notifications", failures, len(deals))
    
    async def discover_new_products(self):
        """Discover and add new trending products"""
        logger.info("Discovering new products...")
        
        added = self.trend_discovery.refresh_product_pool(max_products=30)
        logger.info("Added %s new products to track", added)
        if added == 0:
            logger.warning(
                "No products were added; scrapers may be blocked by anti-bot measures"
            )
    
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
        logger.info("Starting Price Arbitrage Tracker...")
        
        # Start Discord bot
        if self.config.DISCORD_BOT_TOKEN:
            self.start_discord_bot()
        else:
            logger.warning("No Discord token configured, skipping bot startup")
        
        self.setup_scheduler()
        self.scheduler.start()
        logger.info("Scheduler started")
        
        # Keep the bot running
        try:
            while True:
                await asyncio.sleep(60)
        except (KeyboardInterrupt, asyncio.CancelledError):
            logger.info("Shutting down...")
        finally:
            await self.shutdown()

    async def shutdown(self):
        """Stop the scheduler, scrapers and Discord client."""
        if self.scheduler.running:
            self.scheduler.shutdown(wait=False)

        for name, scraper in self.scrapers.items():
            if not hasattr(scraper, 'close'):
                continue
            try:
                scraper.close()
            except Exception:
                logger.exception("Error closing scraper %s", name)

        bot_loop = self.discord_bot.bot_loop
        if bot_loop is not None and not self.discord_bot.is_closed():
            try:
                await asyncio.wrap_future(
                    asyncio.run_coroutine_threadsafe(self.discord_bot.close(), bot_loop)
                )
            except Exception:
                logger.exception("Error closing the Discord client")

def main():
    """Main entry point"""
    configure_logging()

    try:
        tracker = PriceTracker()
    except PriceTrackerError:
        logger.exception("Price Tracker could not start")
        return 1

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    try:
        loop.run_until_complete(tracker.run())
    except KeyboardInterrupt:
        logger.info("Shutting down gracefully...")
    except Exception:
        logger.exception("Price Tracker stopped with an unhandled error")
        return 1
    finally:
        loop.close()
    return 0

if __name__ == "__main__":
    sys.exit(main())
