import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    DISCORD_BOT_TOKEN = os.getenv('DISCORD_BOT_TOKEN')
    
    # Handle channel_id conversion safely
    try:
        DISCORD_CHANNEL_ID = int(os.getenv('DISCORD_CHANNEL_ID', 0))
    except (ValueError, TypeError):
        DISCORD_CHANNEL_ID = 0
    
    EBAY_APP_ID = os.getenv('EBAY_APP_ID')
    EBAY_CERT_ID = os.getenv('EBAY_CERT_ID')
    EBAY_DEV_ID = os.getenv('EBAY_DEV_ID')
    
    BEST_BUY_API_KEY = os.getenv('BEST_BUY_API_KEY')
    
    CHECK_INTERVAL_MINUTES = int(os.getenv('CHECK_INTERVAL_MINUTES', 5))
    MIN_PROFIT_PERCENTAGE = float(os.getenv('MIN_PROFIT_PERCENTAGE', 15))
    EBAY_FEE_PERCENTAGE = float(os.getenv('EBAY_FEE_PERCENTAGE', 13))
    
    # Retailers to track
    RETAILERS = ['bestbuy', 'target', 'homedepot']
    
    # Categories to focus on
    CATEGORIES = ['electronics', 'home_goods', 'appliances', 'tools']
