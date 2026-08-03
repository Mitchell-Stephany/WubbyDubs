"""
Real Products Only - Manual product entry system
Only send notifications for products you manually add with real URLs
"""

import asyncio
import sqlite3
from discord_bot import DiscordBot
from config import Config

def add_real_product():
    """Add a real product with actual URL"""
    print("Add a Real Product to Track")
    print("=" * 50)
    
    name = input("Product name: ").strip()
    if not name:
        print("Product name required")
        return None
    
    url = input("Product URL (must be real): ").strip()
    if not url or 'example.com' in url:
        print("Real product URL required")
        return None
    
    retailer = input("Retailer (e.g., Best Buy, Target, Home Depot): ").strip()
    category = input("Category (e.g., Electronics, Home, Tools): ").strip()
    initial_price = input("Initial price (e.g., 29.99): ").strip()
    
    try:
        initial_price = float(initial_price)
    except:
        print("Invalid price")
        return None
    
    # Add to database
    conn = sqlite3.connect('price_tracker.db')
    cursor = conn.cursor()
    
    # Generate product ID
    product_id = f"manual_{name.replace(' ', '_').lower()}"
    
    try:
        cursor.execute('''
            INSERT INTO products (product_id, retailer, name, url, category)
            VALUES (?, ?, ?, ?, ?)
        ''', (product_id, retailer, name, url, category))
        
        cursor.execute('''
            INSERT INTO prices (product_id, price, timestamp)
            VALUES (?, ?, datetime('now'))
        ''', (product_id, initial_price))
        
        conn.commit()
        print(f"\nProduct added: {name}")
        print(f"URL: {url}")
        print(f"Initial price: ${initial_price:.2f}")
        return product_id
    except sqlite3.IntegrityError:
        print("Product already exists")
        return None
    finally:
        conn.close()

def list_real_products():
    """List all manually added real products"""
    conn = sqlite3.connect('price_tracker.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT * FROM products 
        WHERE product_id LIKE 'manual_%'
        ORDER BY added_at DESC
    ''')
    
    products = [dict(row) for row in cursor.fetchall()]
    conn.close()
    
    if not products:
        print("No real products added yet")
        return []
    
    print("\nYour Real Products:")
    print("=" * 50)
    for i, product in enumerate(products, 1):
        print(f"{i}. {product['name']}")
        print(f"   URL: {product['url']}")
        print(f"   Retailer: {product['retailer']}")
        print(f"   Category: {product['category']}")
        print()
    
    return products

async def send_real_deal_notifications():
    """Send notifications only for real products"""
    print("Checking for deals on real products...")
    
    config = Config()
    discord_bot = DiscordBot(config)
    
    try:
        # Start bot
        bot_task = asyncio.create_task(discord_bot.start_bot())
        await discord_bot.wait_until_ready()
        print("Bot connected")
        
        # Get deals from real products only
        conn = sqlite3.connect('price_tracker.db')
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT d.*, p.name, p.url, p.retailer, p.category
            FROM deals d
            JOIN products p ON d.product_id = p.product_id
            WHERE d.notified = FALSE 
            AND p.product_id LIKE 'manual_%'
            ORDER BY d.timestamp DESC
        ''')
        
        deals = [dict(row) for row in cursor.fetchall()]
        
        if not deals:
            print("No new deals on real products")
            conn.close()
            return
        
        print(f"Found {len(deals)} deals on real products")
        
        # Send notifications
        for deal in deals:
            deal_data = {
                'name': deal['name'],
                'retailer': deal['retailer'],
                'url': deal['url'],
                'category': deal['category'],
                'original_price': deal['original_price'],
                'new_price': deal['new_price'],
                'drop_percentage': deal['drop_percentage'],
                'ebay_price': deal.get('ebay_price'),
                'potential_profit': deal.get('potential_profit'),
                'profit_percentage': deal.get('profit_percentage'),
                'timestamp': deal['timestamp']
            }
            
            await discord_bot.send_deal_notification(deal_data)
            print(f"Sent: {deal['name']} ({deal['drop_percentage']:.1f}% drop)")
            
            # Mark as notified
            cursor.execute('UPDATE deals SET notified = TRUE WHERE id = ?', (deal['id'],))
            conn.commit()
            
            await asyncio.sleep(2)
        
        conn.close()
        print(f"\nSent {len(deals)} real deal notifications!")
        
        await asyncio.sleep(3)
        await discord_bot.close()
        print("Bot closed")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

def main():
    """Main menu"""
    print("=" * 50)
    print("Real Products Only - No Fake Data")
    print("=" * 50)
    
    while True:
        print("\nOptions:")
        print("1. Add a real product")
        print("2. List my real products")
        print("3. Check for deals on real products")
        print("4. Exit")
        
        choice = input("\nChoose option (1-4): ").strip()
        
        if choice == '1':
            add_real_product()
        elif choice == '2':
            list_real_products()
        elif choice == '3':
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                loop.run_until_complete(send_real_deal_notifications())
            finally:
                loop.close()
        elif choice == '4':
            print("Goodbye!")
            break
        else:
            print("Invalid choice")

if __name__ == "__main__":
    main()
