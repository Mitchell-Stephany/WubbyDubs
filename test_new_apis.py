"""
Test script for new free shopping APIs
Tests ShopScout and Shoptera integration
"""

import asyncio
from scrapers import ShopScoutScraper, ShopteraScraper
from config import Config

def test_shopscout():
    """Test ShopScout scraper"""
    print("Testing ShopScout Scraper...")
    print("=" * 50)
    
    config = Config()
    scraper = ShopScoutScraper(config)
    
    # Test with a popular Shopify store
    test_store = 'dbrand.com'
    print(f"Testing with store: {test_store}")
    
    try:
        products = scraper.get_store_products(test_store)
        print(f"Found {len(products)} products")
        
        if products:
            print("\nFirst 3 products:")
            for i, product in enumerate(products[:3], 1):
                print(f"{i}. {product['name']}")
                print(f"   Price: ${product['price']:.2f}")
                print(f"   URL: {product['url']}")
                print()
        
        return len(products) > 0
    except Exception as e:
        print(f"Error: {e}")
        return False

def test_shoptera():
    """Test Shoptera scraper"""
    print("\nTesting Shoptera Scraper...")
    print("=" * 50)
    
    config = Config()
    scraper = ShopteraScraper(config)
    
    # Test with a popular search term
    search_query = 'electronics'
    print(f"Testing with query: {search_query}")
    
    try:
        products = scraper.search_products(search_query, limit=5)
        print(f"Found {len(products)} products")
        
        if products:
            print("\nFirst 3 products:")
            for i, product in enumerate(products[:3], 1):
                print(f"{i}. {product['name']}")
                print(f"   Price: ${product['price']:.2f}")
                print(f"   Store: {product['eshop_name']}")
                print(f"   URL: {product['url']}")
                print()
        
        return len(products) > 0
    except Exception as e:
        print(f"Error: {e}")
        return False

def main():
    """Run all tests"""
    print("Testing New Free Shopping APIs")
    print("=" * 50)
    print()
    
    # Test ShopScout
    shopscout_ok = test_shopscout()
    
    # Test Shoptera
    shoptera_ok = test_shoptera()
    
    # Summary
    print("\n" + "=" * 50)
    print("Test Summary")
    print("=" * 50)
    print(f"ShopScout: {'PASS' if shopscout_ok else 'FAIL'}")
    print(f"Shoptera: {'PASS' if shoptera_ok else 'FAIL'}")
    
    if shopscout_ok and shoptera_ok:
        print("\n[SUCCESS] Both free APIs are working!")
        print("The system can now track products without eBay API")
    else:
        print("\n[WARNING] Some APIs failed, but system can still work with other retailers")

if __name__ == "__main__":
    main()
