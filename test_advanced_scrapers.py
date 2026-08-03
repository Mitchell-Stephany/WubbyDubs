"""
Test advanced scrapers with anti-detection
"""

from config import Config
from scrapers.advanced_target import AdvancedTargetScraper
from scrapers.advanced_homedepot import AdvancedHomeDepotScraper

def test_advanced_target():
    """Test advanced Target scraper"""
    print("Testing Advanced Target Scraper...")
    print("=" * 50)
    
    config = Config()
    scraper = AdvancedTargetScraper(config)
    
    try:
        print("Searching for 'electronics' on Target...")
        products = scraper.search_products('electronics', limit=5)
        print(f"Found {len(products)} products")
        
        if products:
            print("\nFirst 3 products:")
            for i, product in enumerate(products[:3], 1):
                print(f"{i}. {product['name']}")
                print(f"   Price: ${product['price']:.2f}" if product['price'] else "   Price: Not available")
                print(f"   URL: {product['url']}")
                print()
        else:
            print("No products found - may still be blocked")
        
        return len(products) > 0
    except Exception as e:
        print(f"Error: {e}")
        return False
    finally:
        scraper.close()

def test_advanced_homedepot():
    """Test advanced Home Depot scraper"""
    print("\nTesting Advanced Home Depot Scraper...")
    print("=" * 50)
    
    config = Config()
    scraper = AdvancedHomeDepotScraper(config)
    
    try:
        print("Searching for 'tools' on Home Depot...")
        products = scraper.search_products('tools', limit=5)
        print(f"Found {len(products)} products")
        
        if products:
            print("\nFirst 3 products:")
            for i, product in enumerate(products[:3], 1):
                print(f"{i}. {product['name']}")
                print(f"   Price: ${product['price']:.2f}" if product['price'] else "   Price: Not available")
                print(f"   URL: {product['url']}")
                print()
        else:
            print("No products found - may still be blocked")
        
        return len(products) > 0
    except Exception as e:
        print(f"Error: {e}")
        return False
    finally:
        scraper.close()

def main():
    """Run all tests"""
    print("Testing Advanced Scrapers with Anti-Detection")
    print("=" * 50)
    print()
    
    # Test Target
    target_ok = test_advanced_target()
    
    # Test Home Depot
    homedepot_ok = test_advanced_homedepot()
    
    # Summary
    print("\n" + "=" * 50)
    print("Test Summary")
    print("=" * 50)
    print(f"Advanced Target: {'PASS' if target_ok else 'FAIL'}")
    print(f"Advanced Home Depot: {'PASS' if homedepot_ok else 'FAIL'}")
    
    if target_ok or homedepot_ok:
        print("\n[SUCCESS] Advanced scrapers are working!")
        print("Automatic product discovery should now work")
    else:
        print("\n[WARNING] Advanced scrapers still facing detection")
        print("Consider using official APIs for reliable access")

if __name__ == "__main__":
    main()
