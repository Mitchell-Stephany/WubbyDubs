"""
Run the price tracking system with Discord notifications
DISABLED - Use real_products_only.py for real products only
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

def run_system():
    """Run the price tracking system"""
    print("=" * 50)
    print("PRICE TRACKING SYSTEM - DISABLED")
    print("=" * 50)
    print("\nAutomatic product discovery has been DISABLED")
    print("to prevent fake links and fake products.")
    print("\nUse: python real_products_only.py")
    print("to add REAL products with REAL URLs manually.")
    print("\nThis ensures:")
    print("  - Only real product URLs")
    print("  - Only products you choose")
    print("  - No fake data spam")
    print("=" * 50)

if __name__ == "__main__":
    run_system()
