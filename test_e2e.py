"""
End-to-end test with eBay arbitrage calculation
"""
import asyncio
import sqlite3
from database import Database
from scrapers.browser_scraper import BrowserScraper
from scrapers.ebay_sold_scraper import eBaySoldScraper
from price_analyzer import PriceAnalyzer
from config import Config
from ebay_api import eBayAPI

async def test_e2e():
    print("=" * 60)
    print("  END-TO-END TEST WITH EBAY ARBITRAGE")
    print("=" * 60)
    
    config = Config()
    db = Database()
    ebay_api = eBayAPI(config)
    scraper = BrowserScraper(config, headless=True)
    
    # Clear old data
    print("\n1. Clearing database...")
    with sqlite3.connect(db.db_path) as conn:
        conn.execute("DELETE FROM price_history")
        conn.execute("DELETE FROM deals")
        conn.execute("DELETE FROM products")
        conn.commit()
    
    # Discover products
    print("\n2. Discovering products...")
    await scraper._start()
    
    queries = ['wireless earbuds', 'usb-c hub']
    for query in queries:
        print(f"\n   Searching for '{query}'...")
        products = await scraper.search_all_retailers(query, limit_per_retailer=2)
        for product in products:
            if product['price'] > 0 and product['url']:
                db.add_product(
                    product_id=product['product_id'],
                    retailer=product['retailer'],
                    name=product['name'],
                    url=product['url'],
                    category=product.get('category', 'General')
                )
                db.update_price(product['product_id'], product['price'])
                print(f"   Added: {product['name'][:50]} - ${product['price']:.2f} ({product['retailer']})")
        await asyncio.sleep(3)
    
    # Simulate price drops
    print("\n3. Simulating price drops...")
    all_products = db.get_all_products()
    for product in all_products[:3]:
        current = db.get_latest_price(product['product_id'])
        if current and current > 5:
            new_price = current * 0.5  # 50% drop - big enough to potentially be profitable
            db.update_price(product['product_id'], new_price)
            print(f"   {product['name'][:40]}: ${current:.2f} -> ${new_price:.2f}")
    
    # Analyze with eBay
    print("\n4. Analyzing with eBay arbitrage calculation...")
    analyzer = PriceAnalyzer(config, db, ebay_api, scraper)
    deals = await analyzer.analyze_all_products_with_ebay()
    
    print(f"\n   Deals found: {len(deals)}")
    for deal in deals:
        print(f"\n   {'=' * 50}")
        print(f"   Product: {deal['name'][:50]}")
        print(f"   Retailer: {deal['retailer']}")
        print(f"   Price: ${deal['original_price']:.2f} -> ${deal['new_price']:.2f} ({deal['drop_percentage']:.1f}% drop)")
        if deal.get('ebay_price'):
            print(f"   eBay est. sale: ${deal['ebay_price']:.2f}")
            print(f"   eBay range: {deal.get('ebay_price_range', 'N/A')}")
            print(f"   Profit: ${deal['potential_profit']:.2f}")
            print(f"   Confidence: {deal.get('ebay_confidence')} ({deal.get('sample_size')} samples)")
            print(f"   Arbitrage: {'YES' if deal.get('is_arbitrage') else 'NO'}")
        else:
            print(f"   No eBay data (fallback mode)")
    
    await scraper.close()
    
    print("\n" + "=" * 60)
    print("  TEST COMPLETE")
    print("=" * 60)

asyncio.run(test_e2e())
