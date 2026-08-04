"""Test eBay sold listings scraper"""
import asyncio
from scrapers.browser_scraper import BrowserScraper
from scrapers.ebay_sold_scraper import eBaySoldScraper

async def test():
    print("Testing eBay Sold Listings Scraper")
    print("=" * 60)
    
    scraper = BrowserScraper(headless=True)
    try:
        await scraper._start()
        ebay = eBaySoldScraper(scraper)
        
        # Test products
        test_products = [
            ("JLab Go Air Pop Bluetooth Earbuds", 19.88),
            ("Vivitar Multi-Port USB Hub", 29.88),
            ("Wireless Earbuds Bluetooth Headphone 60H Deep Bass", 16.39),
        ]
        
        for product_name, retail_price in test_products:
            print(f"\n{'=' * 60}")
            print(f"Product: {product_name[:50]}")
            print(f"Retail price: ${retail_price:.2f}")
            print(f"{'=' * 60}")
            
            result = await ebay.calculate_arbitrage_profit(
                product_name,
                retail_price,
                ebay_fee_percentage=13.0
            )
            
            if result:
                print(f"\n  eBay estimated sale price: ${result['estimated_ebay_price']:.2f}")
                print(f"  eBay price range: {result['ebay_price_range']}")
                print(f"  Sample size: {result['sample_size']} sold listings")
                print(f"  Confidence: {result['ebay_confidence']}")
                print(f"  eBay fees (13%): ${result['fees']:.2f}")
                print(f"  Estimated profit: ${result['profit']:.2f}")
                print(f"  Profit margin: {result['profit_percentage']:.1f}%")
                print(f"  ROI: {result['roi']:.1f}%")
                print(f"  Profitable: {'YES' if result['is_profitable'] else 'NO'}")
            else:
                print("\n  No eBay sold listings found")
            
            await asyncio.sleep(3)
    
    finally:
        await scraper.close()
    
    print("\n" + "=" * 60)
    print("Test complete")

asyncio.run(test())
