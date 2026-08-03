"""
Basic test to check if the system components work
"""

from config import Config
from database import Database
from scrapers import TargetScraper, HomeDepotScraper

def test_basic():
    print("Testing basic system components...")
    print("=" * 50)
    
    # Test configuration
    print("1. Testing Configuration...")
    try:
        config = Config()
        print(f"   Discord Channel ID: {config.DISCORD_CHANNEL_ID}")
        print(f"   eBay Enabled: {config.EBAY_ENABLED}")
        print(f"   Best Buy Enabled: {config.BEST_BUY_ENABLED}")
        print(f"   Retailers: {config.RETAILERS}")
        print("   [OK] Configuration loaded")
    except Exception as e:
        print(f"   [ERROR] Configuration failed: {e}")
        return False
    
    # Test database
    print("\n2. Testing Database...")
    try:
        db = Database('test_basic.db')
        print("   [OK] Database initialized")
        import os
        os.remove('test_basic.db')
    except Exception as e:
        print(f"   [ERROR] Database failed: {e}")
        return False
    
    # Test scrapers
    print("\n3. Testing Scrapers...")
    try:
        config = Config()
        target = TargetScraper(config)
        homedepot = HomeDepotScraper(config)
        print("   [OK] Scrapers initialized")
    except Exception as e:
        print(f"   [ERROR] Scrapers failed: {e}")
        return False
    
    print("\n" + "=" * 50)
    print("[SUCCESS] All basic components are working!")
    print("The main system should be able to start.")
    return True

if __name__ == "__main__":
    test_basic()
