"""
Test script for Discord bot connectivity
This tests Discord without requiring other APIs
"""

import asyncio
import os
from dotenv import load_dotenv
from discord_bot import DiscordBot
from config import Config

async def test_discord():
    """Test Discord bot connection and send a test notification"""
    print("Testing Discord Bot Connection...")
    print("=" * 50)
    
    # Load environment variables
    load_dotenv()
    
    # Check for Discord credentials
    token = os.getenv('DISCORD_BOT_TOKEN')
    channel_id = os.getenv('DISCORD_CHANNEL_ID')
    
    if not token or token == 'your_discord_bot_token_here':
        print("[ERROR] Discord bot token not configured in .env file")
        print("Please add your DISCORD_BOT_TOKEN to the .env file")
        return False
    
    if not channel_id or channel_id == 'your_channel_id_here':
        print("[ERROR] Discord channel ID not configured in .env file")
        print("Please add your DISCORD_CHANNEL_ID to the .env file")
        return False
    
    print("[OK] Discord bot token found")
    print(f"[OK] Channel ID: {channel_id}")
    
    # Initialize bot
    try:
        config = Config()
        bot = DiscordBot(config)
        print("[OK] Discord bot initialized")
    except Exception as e:
        print(f"[ERROR] Failed to initialize bot: {e}")
        return False
    
    # Start the bot
    print("\nStarting Discord bot...")
    print("(Note: This may take a few seconds)")
    
    # Run bot in background
    bot_task = asyncio.create_task(bot.start_bot())
    
    # Wait for bot to be ready
    try:
        await asyncio.wait_for(bot.wait_until_ready(), timeout=30)
        print("[OK] Discord bot connected successfully!")
    except asyncio.TimeoutError:
        print("[ERROR] Bot failed to connect within 30 seconds")
        return False
    except Exception as e:
        print(f"[ERROR] Bot connection failed: {e}")
        return False
    
    # Send test notification
    print("\nSending test notification...")
    test_deal = {
        'name': 'Test Product - Sony WH-1000XM5 Headphones',
        'retailer': 'bestbuy',
        'category': 'electronics',
        'url': 'https://bestbuy.com',
        'original_price': 349.99,
        'new_price': 249.99,
        'drop_percentage': 28.6,
        'ebay_price': 320.00,
        'potential_profit': 27.30,
        'profit_percentage': 10.9,
        'timestamp': 'Test run'
    }
    
    try:
        await bot.send_deal_notification(test_deal)
        print("[OK] Test notification sent successfully!")
        print("\nPlease check your Discord channel for the test message.")
    except Exception as e:
        print(f"[ERROR] Failed to send notification: {e}")
        return False
    
    # Wait a bit for the message to be delivered
    print("\nWaiting 5 seconds to ensure message delivery...")
    await asyncio.sleep(5)
    
    # Close the bot
    print("\nClosing Discord bot...")
    await bot.close()
    
    print("\n" + "=" * 50)
    print("Discord test completed successfully!")
    print("=" * 50)
    return True

def main():
    """Main entry point"""
    try:
        success = asyncio.run(test_discord())
        if success:
            print("\n[SUCCESS] Discord integration is working correctly!")
            print("You can now add your eBay and Best Buy API keys to .env")
            print("Then run the main application with: python main.py")
        else:
            print("\n[FAILED] Discord test failed. Please check the errors above.")
    except KeyboardInterrupt:
        print("\nTest interrupted by user")
    except Exception as e:
        print(f"\nUnexpected error: {e}")

if __name__ == "__main__":
    main()
