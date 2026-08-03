"""
Test multi-source scraper for reliable product discovery
"""

from config import Config
from scrapers.multi_source import MultiSourceScraper

def test_multi_source():
    """Test multi-source scraper"""
    print("Testing Multi-Source Scraper...")
    print("=" * 50)
    
    config = Config()
    scraper = MultiSourceScraper(config)
    
    try:
        print("Getting trending products...")
        products = scraper.get_trending_products(limit=10)
        print(f"Found {len(products)} products")
        
        if products:
            print("\nFirst 5 products:")
            for i, product in enumerate(products[:5], 1):
                print(f"{i}. {product['name']}")
                print(f"   Price: ${product['price']:.2f}")
                print(f"   Category: {product['category']}")
                print(f"   Product ID: {product['product_id']}")
                print()
            
            # Test price tracking
            print("Testing price tracking for first product...")
            first_product_id = products[0]['product_id']
            initial_price = scraper.get_product_price(first_product_id)
            print(f"Initial price: ${initial_price:.2f}")
            
            # Simulate some price checks
            for i in range(3):
                new_price = scraper.get_product_price(first_product_id)
                print(f"Check {i+1}: ${new_price:.2f}")
            
            return len(products) > 0
        else:
            print("No products found")
            return False
            
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run test"""
    print("Testing Multi-Source Product Discovery")
    print("=" * 50)
    print()
    
    success = test_multi_source()
    
    print("\n" + "=" * 50)
    print("Test Summary")
    print("=" * 50)
    print(f"Multi-Source Scraper: {'PASS' if success else 'FAIL'}")
    
    if success:
        print("\n[SUCCESS] Multi-source scraper is working!")
        print("The system can now automatically discover and track products")
    else:
        print("\n[FAILED] Multi-source scraper failed")

if __name__ == "__main__":
    main()
