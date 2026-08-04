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
    
    # API keys disabled - using high-fidelity scrapers only
    EBAY_ENABLED = False
    BEST_BUY_ENABLED = False
    BUYWHERE_ENABLED = False
    
    CHECK_INTERVAL_MINUTES = int(os.getenv('CHECK_INTERVAL_MINUTES', 5))
    MIN_PROFIT_PERCENTAGE = float(os.getenv('MIN_PROFIT_PERCENTAGE', 15))
    EBAY_FEE_PERCENTAGE = float(os.getenv('EBAY_FEE_PERCENTAGE', 13))
    
    # Retailers to track with high-fidelity scrapers
    RETAILERS = ['target', 'walmart', 'amazon', 'homedepot', 'lowes']
    
    # Categories to focus on
    CATEGORIES = ['electronics', 'home_goods', 'appliances', 'tools', 'clothing', 'fitness', 'beauty']
    
    # Fallback mode (no eBay API)
    FALLBACK_MODE = True
    
    # Advanced scraping mode with anti-detection
    ADVANCED_SCRAPING = True
    
    # Anti-detection settings
    USER_AGENTS = [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15'
    ]
    
    # Request delays (seconds)
    MIN_DELAY = 2
    MAX_DELAY = 5
    
    # Proxy settings (optional)
    USE_PROXIES = False
    PROXY_LIST = []
