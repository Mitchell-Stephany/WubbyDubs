"""
Quick Discord notification for REAL deals only
No fake products - only manually added real products
"""

import asyncio
import sqlite3
from discord_bot import DiscordBot
from config import Config

async def send_actual_deals():
    """Send actual deal notifications from database (real products only)"""
    print("Sending deal notifications for REAL products only...")
    
    config = Config()
    discord_bot = DiscordBot(config)
    
    try:
        # Start bot
        bot_task = asyncio.create_task(discord_bot.start_bot())
        await discord_bot.wait_until_ready()
        print("Bot connected")
        
        # Get recent deals from database
        conn = sqlite3.connect('price_tracker.db')
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Only get deals that haven't been notified AND are real products (manual entry)
        cursor.execute('''
            SELECT d.*, p.name, p.url, p.retailer, p.category
            FROM deals d
            JOIN products p ON d.product_id = p.product_id
            WHERE d.notified = FALSE 
            AND p.product_id LIKE 'manual_%'
            ORDER BY d.timestamp DESC
            LIMIT 5
        ''')
        
        deals = [dict(row) for row in cursor.fetchall()]
        
        if not deals:
            print("No new deals to send on real products")
            conn.close()
            print("Use: python real_products_only.py to add real products")
            return
        
        print(f"Found {len(deals)} new deals to send")
        
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
        print(f"\nSent {len(deals)} deal notifications!")
        
        await asyncio.sleep(3)
        await discord_bot.close()
        print("Bot closed")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

def main():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(send_actual_deals())
    finally:
        loop.close()

if __name__ == "__main__":
    main()


