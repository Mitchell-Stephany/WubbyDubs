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
    
    # eBay API (optional)
    EBAY_APP_ID = os.getenv('EBAY_APP_ID')
    EBAY_CERT_ID = os.getenv('EBAY_CERT_ID')
    EBAY_DEV_ID = os.getenv('EBAY_DEV_ID')
    EBAY_ENABLED = bool(EBAY_APP_ID and EBAY_CERT_ID and EBAY_DEV_ID and 
                       EBAY_APP_ID != 'your_ebay_app_id_here' and
                       EBAY_CERT_ID != 'your_ebay_cert_id_here' and
                       EBAY_DEV_ID != 'your_ebay_dev_id_here')
    
    # Best Buy API (optional)
    BEST_BUY_API_KEY = os.getenv('BEST_BUY_API_KEY')
    BEST_BUY_ENABLED = bool(BEST_BUY_API_KEY and BEST_BUY_API_KEY != 'your_best_buy_api_key_here')
    
    CHECK_INTERVAL_MINUTES = int(os.getenv('CHECK_INTERVAL_MINUTES', 5))
    MIN_PROFIT_PERCENTAGE = float(os.getenv('MIN_PROFIT_PERCENTAGE', 15))
    EBAY_FEE_PERCENTAGE = float(os.getenv('EBAY_FEE_PERCENTAGE', 13))
    
    # Retailers to track (using multi-source approach for reliability)
    RETAILERS = ['multi_source']  # Using multi-source for reliable product discovery
    
    # Note: Web scraping may face anti-bot measures from retailers
    # Consider using official APIs when available
    
    # Shopify stores for ShopScout (if API becomes available)
    SHOPIFY_STORES = [
        'gymshark.com',
        'allbirds.com', 
        'kyliecosmetics.com',
        'fashionnova.com',
        'dbrand.com'
    ]
    
    # Categories to focus on
    CATEGORIES = ['electronics', 'home_goods', 'appliances', 'tools', 'clothing', 'fitness', 'beauty']
    
    # Fallback mode (when eBay is not available)
    FALLBACK_MODE = not EBAY_ENABLED
    
    # Advanced scraping mode (uses Selenium for better anti-detection)
    ADVANCED_SCRAPING = os.getenv('ADVANCED_SCRAPING', 'true').lower() == 'true'
