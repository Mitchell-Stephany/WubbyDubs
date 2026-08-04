"""
Clean database - remove all fake products and deals
"""

import sqlite3

def clean_database():
    """Remove all fake products and deals from database"""
    print("Cleaning database - removing fake products...")
    print("=" * 50)
    
    conn = sqlite3.connect('price_tracker.db')
    cursor = conn.cursor()
    
    # Check what's in the database
    cursor.execute('SELECT COUNT(*) FROM products')
    total_products = cursor.fetchone()[0]
    print(f"Total products in database: {total_products}")
    
    cursor.execute('SELECT COUNT(*) FROM products WHERE product_id LIKE "manual_%"')
    real_products = cursor.fetchone()[0]
    print(f"Real products (manual): {real_products}")
    
    cursor.execute('SELECT COUNT(*) FROM products WHERE product_id LIKE "generic_%"')
    fake_products = cursor.fetchone()[0]
    print(f"Fake products (generic): {fake_products}")
    
    cursor.execute('SELECT COUNT(*) FROM products WHERE product_id LIKE "buywhere_%"')
    buywhere_products = cursor.fetchone()[0]
    print(f"BuyWhere products: {buywhere_products}")
    
    # Remove fake products
    print("\nRemoving fake products...")
    cursor.execute('DELETE FROM products WHERE product_id LIKE "generic_%"')
    deleted_products = cursor.rowcount
    print(f"Deleted {deleted_products} fake products")
    
    # Remove BuyWhere products
    cursor.execute('DELETE FROM products WHERE product_id LIKE "buywhere_%"')
    deleted_buywhere = cursor.rowcount
    print(f"Deleted {deleted_buywhere} BuyWhere products")
    
    # Remove fake price history
    cursor.execute('DELETE FROM price_history WHERE product_id LIKE "generic_%"')
    deleted_prices = cursor.rowcount
    print(f"Deleted {deleted_prices} fake price history records")
    
    # Remove BuyWhere price history
    cursor.execute('DELETE FROM price_history WHERE product_id LIKE "buywhere_%"')
    deleted_buywhere_prices = cursor.rowcount
    print(f"Deleted {deleted_buywhere_prices} BuyWhere price history records")
    
    # Remove fake deals
    cursor.execute('DELETE FROM deals WHERE product_id LIKE "generic_%"')
    deleted_deals = cursor.rowcount
    print(f"Deleted {deleted_deals} fake deal records")
    
    # Remove BuyWhere deals
    cursor.execute('DELETE FROM deals WHERE product_id LIKE "buywhere_%"')
    deleted_buywhere_deals = cursor.rowcount
    print(f"Deleted {deleted_buywhere_deals} BuyWhere deal records")
    
    # Check for example.com URLs
    cursor.execute('SELECT COUNT(*) FROM products WHERE url LIKE "%example.com%"')
    example_count = cursor.fetchone()[0]
    if example_count > 0:
        print(f"\nFound {example_count} products with example.com URLs")
        cursor.execute('DELETE FROM products WHERE url LIKE "%example.com%"')
        print("Deleted products with example.com URLs")
    
    conn.commit()
    
    # Show final state
    cursor.execute('SELECT COUNT(*) FROM products')
    final_products = cursor.fetchone()[0]
    cursor.execute('SELECT name, url FROM products WHERE product_id LIKE "manual_%"')
    remaining = cursor.fetchall()
    
    print("\n" + "=" * 50)
    print("Database cleanup complete!")
    print(f"Remaining products: {final_products}")
    
    if remaining:
        print("\nRemaining products:")
        for name, url in remaining:
            print(f"  - {name}: {url}")
    else:
        print("Database is now clean - ready for real products only")
    
    conn.close()
    print("=" * 50)

if __name__ == "__main__":
    clean_database()
