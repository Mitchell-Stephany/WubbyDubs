"""
Send recent deals to Discord
"""

import asyncio
from database import Database
from discord_bot import DiscordBot
from config import Config

async def send_recent_deals():
    """Send recent deals from database to Discord"""
    print("Sending recent deals to Discord...")
    print("=" * 50)
    
    config = Config()
    db = Database()
    discord_bot = DiscordBot(config)
    
    if not config.DISCORD_BOT_TOKEN:
        print("No Discord token configured")
        return
    
    try:
        # Start Discord bot
        print("Starting Discord bot...")
        await discord_bot.start_bot()
        await discord_bot.wait_until_ready()
        print("Discord bot connected")
        
        # Get recent deals from database
        import sqlite3
        conn = sqlite3.connect('price_tracker.db')
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Get recent deals that haven't been notified
        cursor.execute('''
            SELECT d.*, p.name, p.url, p.retailer, p.category
            FROM deals d
            JOIN products p ON d.product_id = p.product_id
            WHERE d.notified = FALSE
            ORDER BY d.timestamp DESC
            LIMIT 10
        ''')
        
        deals = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        if not deals:
            print("No new deals to send")
            return
        
        print(f"Found {len(deals)} new deals to send")
        
        # Send each deal
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
            print(f"Sent: {deal['name']}")
            await asyncio.sleep(1)
            
            # Mark as notified
            conn = sqlite3.connect('price_tracker.db')
            cursor = conn.cursor()
            cursor.execute('UPDATE deals SET notified = TRUE WHERE id = ?', (deal['id'],))
            conn.commit()
            conn.close()
        
        print(f"\nSent {len(deals)} deal notifications to Discord")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await discord_bot.close()
        print("Discord bot closed")

def main():
    """Main entry point"""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(send_recent_deals())
    finally:
        loop.close()

if __name__ == "__main__":
    main()
