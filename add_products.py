"""
Manual product addition tool
Add specific products to track manually
"""

import logging

from config import Config
from database import Database
from exceptions import PriceTrackerError
from logging_config import configure_logging
from scrapers import TargetScraper, HomeDepotScraper

logger = logging.getLogger(__name__)

def add_manual_product():
    """Manually add a product to track"""
    print("Manual Product Addition")
    print("=" * 50)
    
    config = Config()
    db = Database()
    
    print("\nAvailable retailers:")
    print("1. Target")
    print("2. Home Depot")
    
    retailer_choice = input("\nSelect retailer (1-2): ").strip()
    
    if retailer_choice == '1':
        retailer = 'target'
        scraper = TargetScraper(config)
        print("\nEnter Target product URL or TCIN:")
        print("Example: https://www.target.com/p/PRODUCT_ID or TCIN number")
    elif retailer_choice == '2':
        retailer = 'homedepot'
        scraper = HomeDepotScraper(config)
        print("\nEnter Home Depot product URL or product ID:")
        print("Example: https://www.homedepot.com/p/PRODUCT_ID")
    else:
        print("Invalid choice")
        return
    
    product_input = input("Product URL or ID: ").strip()
    
    # Extract product ID from URL if needed
    if '/' in product_input:
        # It's a URL, try to extract ID
        if '/p/' in product_input:
            product_id = product_input.split('/p/')[-1].split('/')[0]
        else:
            product_id = product_input.split('/')[-1]
    else:
        product_id = product_input
    
    print(f"\nFetching product info for {product_id}...")
    
    try:
        product_info = scraper.get_product_info(product_id)
        
        if product_info and product_info.get('name'):
            print(f"Found: {product_info['name']}")
            print(f"Price: ${product_info.get('price', 0):.2f}")
            print(f"Category: {product_info.get('category', 'Unknown')}")
            
            confirm = input("\nAdd this product to tracking? (y/n): ").strip().lower()
            
            if confirm == 'y':
                db.add_product(
                    product_id=product_id,
                    retailer=retailer,
                    name=product_info['name'],
                    url=product_info.get('url', product_input),
                    category=product_info.get('category', 'Unknown')
                )
                
                # Record initial price
                if product_info.get('price'):
                    db.update_price(product_id, product_info['price'])
                
                print(f"\n[SUCCESS] Product added to tracking!")
                print(f"Product ID: {product_id}")
                print(f"Retailer: {retailer}")
            else:
                print("Product not added")
        else:
            print("Could not fetch product information")
            print("The retailer may have anti-scraping measures or the product ID is invalid")
            
    except PriceTrackerError:
        logger.exception("Could not add %s from %s", product_id, retailer)
        print("The retailer may have anti-scraping measures")

def main():
    """Main function"""
    configure_logging()

    while True:
        add_manual_product()
        
        another = input("\nAdd another product? (y/n): ").strip().lower()
        if another != 'y':
            break
    
    print("\nDone! You can now run python main.py to start tracking.")

if __name__ == "__main__":
    main()
