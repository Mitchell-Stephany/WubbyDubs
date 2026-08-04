"""
Test BuyWhere API integration
"""

from config import Config
from scrapers.buywhere import BuyWhereScraper

def test_buywhere():
    """Test BuyWhere API"""
    print("Testing BuyWhere API Integration")
    print("=" * 50)
    
    config = Config()
    
    if not config.BUYWHERE_ENABLED:
        print("BuyWhere API not enabled")
        print("Check your .env file for BUYWHERE_API_KEY")
        return False
    
    print(f"BuyWhere API key found: {config.BUYWHERE_API_KEY[:10]}...")
    
    scraper = BuyWhereScraper(config)
    
    # Test search
    print("\n1. Testing product search...")
    products = scraper.search_products("wireless earbuds", limit=5)
    print(f"Found {len(products)} products")
    
    if products:
        print("\nFirst 3 products:")
        for i, product in enumerate(products[:3], 1):
            print(f"{i}. {product['name']}")
            print(f"   Price: ${product['price']:.2f}")
            print(f"   Retailer: {product['retailer']}")
            print(f"   URL: {product['url']}")
            print(f"   Category: {product['category']}")
            print()
        
        # Test trending products
        print("2. Testing trending products...")
        trending = scraper.get_trending_products(limit=5)
        print(f"Found {len(trending)} trending products")
        
        if trending:
            print("\nFirst 3 trending products:")
            for i, product in enumerate(trending[:3], 1):
                print(f"{i}. {product['name']}")
                print(f"   Price: ${product['price']:.2f}")
                print(f"   Retailer: {product['retailer']}")
                print()
        
        return True
    else:
        print("No products found - API may not be working")
        return False

def main():
    """Run test"""
    success = test_buywhere()
    
    print("\n" + "=" * 50)
    print("Test Summary")
    print("=" * 50)
    print(f"BuyWhere API: {'PASS' if success else 'FAIL'}")
    
    if success:
        print("\n[SUCCESS] BuyWhere API is working!")
        print("The system can now discover real products from Amazon, Best Buy, Walmart")
    else:
        print("\n[FAILED] BuyWhere API integration failed")

if __name__ == "__main__":
    main()
