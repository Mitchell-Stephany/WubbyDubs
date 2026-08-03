"""
Test imports one by one to find where it's getting stuck
"""

print("Testing imports...")

print("1. Importing asyncio...")
import asyncio
print("   OK")

print("2. Importing config...")
from config import Config
print("   OK")

print("3. Importing database...")
from database import Database
print("   OK")

print("4. Importing scrapers...")
from scrapers import BestBuyScraper, TargetScraper, HomeDepotScraper
print("   OK")

print("5. Importing eBay API...")
from ebay_api import eBayAPI
print("   OK")

print("6. Importing Discord bot...")
from discord_bot import DiscordBot
print("   OK")

print("7. Importing price analyzer...")
from price_analyzer import PriceAnalyzer
print("   OK")

print("8. Importing trend discovery...")
from trend_discovery import TrendDiscovery
print("   OK")

print("9. Importing APScheduler...")
from apscheduler.schedulers.asyncio import AsyncIOScheduler
print("   OK")

print("\nAll imports successful!")
