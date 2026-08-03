"""
Simplified main system that focuses on core functionality
"""

import asyncio
import logging
import sys
import time
from datetime import datetime

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

class SimplifiedPriceTracker:
    """Simplified price tracking system"""
    
    def __init__(self):
        logger.info("Initializing Price Tracker...")
        self.config = Config()
        self.db = Database()
        self.scraper = MultiSourceScraper(self.config)
        self.ebay_api = eBayAPI(self.config)
        self.price_analyzer = PriceAnalyzer(self.config, self.db, self.ebay_api)
        self.trend_discovery = TrendDiscovery(self.config, self.db)
        self.discord_bot = DiscordBot(self.config)
        logger.info("Price Tracker initialized")
    
    def update_all_prices(self):
        """Refresh the stored price of every tracked product."""
        products = self.db.get_all_products()
        logger.info("Checking %s products...", len(products))
        failures = 0

        for product in products:
            try:
                current_price = self.scraper.get_product_price(product['product_id'])
                if current_price:
                    self.db.update_price(product['product_id'], current_price)
                    logger.info("Updated price for %s: $%.2f", product['name'], current_price)
            except PriceTrackerError:
                logger.exception("Error checking price for %s", product['name'])
                failures += 1

        if failures:
            logger.error("Price check failed for %s of %s products", failures, len(products))
        return products

    def check_and_notify(self):
        """Check prices and report deals"""
        logger.info("[%s] Starting price check...", datetime.now())

        self.update_all_prices()
        
        # Analyze for deals
        logger.info("Analyzing for deals...")
        deals = self.price_analyzer.analyze_all_products()
        
        if deals:
            logger.info("Found %s potential deals!", len(deals))
            for deal in deals:
                logger.info(
                    "Deal: %s - %.1f%% drop ($%.2f -> $%.2f)",
                    deal['name'], deal['drop_percentage'],
                    deal['original_price'], deal['new_price']
                )
        else:
            logger.info("No new deals found")
    
    def discover_products(self):
        """Discover new products"""
        logger.info("[%s] Discovering new products...", datetime.now())
        added = self.trend_discovery.refresh_product_pool(max_products=10)
        logger.info("Added %s new products to track", added)
    
    async def _notify(self, deals):
        """Start the bot, deliver every deal, then close it again."""
        bot_task = asyncio.create_task(self.discord_bot.start_bot())
        try:
            await self.discord_bot.wait_until_ready()

            failures = 0
            for deal in deals:
                try:
                    await self.discord_bot.send_deal_notification(deal)
                except NotificationError:
                    logger.exception("Could not notify about %s", deal.get('name'))
                    failures += 1
                await asyncio.sleep(1)

            if failures:
                raise NotificationError(
                    f"Failed to deliver {failures} of {len(deals)} deal notifications"
                )
        finally:
            await self.discord_bot.close()
            bot_task.cancel()

    def run_once(self):
        """Run a single check cycle"""
        logger.info("=== Single Check Cycle ===")
        
        # Discover products
        self.discover_products()
        
        # Check prices and notify
        self.check_and_notify()
        
        products = self.update_all_prices()
        if not products:
            logger.info("Check cycle completed")
            return

        deals = self.price_analyzer.analyze_all_products()

        if not deals:
            logger.info("Check cycle completed")
            return

        if not self.config.DISCORD_BOT_TOKEN:
            logger.warning("Discord is not configured; %s deals were not sent", len(deals))
            logger.info("Check cycle completed")
            return

        logger.info("Sending Discord notifications...")
        try:
            asyncio.run(self._notify(deals))
            logger.info("Discord notifications sent")
        except (NotificationError, PriceTrackerError):
            logger.exception("Discord notification failed")

        logger.info("Check cycle completed")
    
    def run_continuous(self, interval_minutes=5):
        """Run continuous monitoring"""
        logger.info("Starting continuous monitoring (every %s minutes)...", interval_minutes)
        print("Press Ctrl+C to stop")
        
        try:
            while True:
                self.run_once()
                logger.info("Waiting %s minutes until next check...", interval_minutes)
                time.sleep(interval_minutes * 60)
        except KeyboardInterrupt:
            logger.info("Stopping...")

def main():
    """Main entry point"""
    configure_logging()

    try:
        tracker = SimplifiedPriceTracker()
    except PriceTrackerError:
        logger.exception("Price Tracker could not start")
        return 1
    
    print("\nChoose mode:")
    print("1. Single check (one-time)")
    print("2. Continuous monitoring")
    
    choice = input("Enter choice (1-2): ").strip()
    
    try:
        if choice == '1':
            tracker.run_once()
        elif choice == '2':
            interval = input("Check interval in minutes (default 5): ").strip()
            interval = int(interval) if interval else 5
            tracker.run_continuous(interval)
        else:
            print("Invalid choice")
            return 1
    except PriceTrackerError:
        logger.exception("Price Tracker stopped with an error")
        return 1
    return 0

if __name__ == "__main__":
    sys.exit(main())
