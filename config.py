import logging
import os
from dotenv import load_dotenv

from exceptions import ConfigError

load_dotenv()

logger = logging.getLogger(__name__)

PLACEHOLDERS = {
    'EBAY_APP_ID': 'your_ebay_app_id_here',
    'EBAY_CERT_ID': 'your_ebay_cert_id_here',
    'EBAY_DEV_ID': 'your_ebay_dev_id_here',
    'BEST_BUY_API_KEY': 'your_best_buy_api_key_here',
    'DISCORD_BOT_TOKEN': 'your_discord_bot_token_here',
    'DISCORD_CHANNEL_ID': 'your_channel_id_here',
}


def _env_value(name: str):
    """Return the environment value, treating the .env.example placeholder as unset."""
    value = os.getenv(name)
    if value is None:
        return None
    value = value.strip()
    if not value or value == PLACEHOLDERS.get(name):
        return None
    return value


def _env_number(name: str, default, cast):
    """Parse a numeric setting, failing loudly instead of crashing with a bare ValueError."""
    raw = _env_value(name)
    if raw is None:
        return default
    try:
        return cast(raw)
    except ValueError as exc:
        raise ConfigError(
            f"{name} must be a {cast.__name__}, got {raw!r}"
        ) from exc


def _channel_id() -> int:
    raw = _env_value('DISCORD_CHANNEL_ID')
    if raw is None:
        return 0
    try:
        return int(raw)
    except ValueError as exc:
        raise ConfigError(
            f"DISCORD_CHANNEL_ID must be a numeric Discord channel ID, got {raw!r}"
        ) from exc


class Config:
    DISCORD_BOT_TOKEN = _env_value('DISCORD_BOT_TOKEN')
    DISCORD_CHANNEL_ID = _channel_id()

    # eBay API (optional)
    EBAY_APP_ID = _env_value('EBAY_APP_ID')
    EBAY_CERT_ID = _env_value('EBAY_CERT_ID')
    EBAY_DEV_ID = _env_value('EBAY_DEV_ID')
    EBAY_ENABLED = bool(EBAY_APP_ID and EBAY_CERT_ID and EBAY_DEV_ID)

    # Best Buy API (optional)
    BEST_BUY_API_KEY = _env_value('BEST_BUY_API_KEY')
    BEST_BUY_ENABLED = bool(BEST_BUY_API_KEY)

    CHECK_INTERVAL_MINUTES = _env_number('CHECK_INTERVAL_MINUTES', 5, int)
    MIN_PROFIT_PERCENTAGE = _env_number('MIN_PROFIT_PERCENTAGE', 15.0, float)
    EBAY_FEE_PERCENTAGE = _env_number('EBAY_FEE_PERCENTAGE', 13.0, float)

    # Timeout applied to every outbound HTTP request made by scrapers (seconds)
    REQUEST_TIMEOUT_SECONDS = _env_number('REQUEST_TIMEOUT_SECONDS', 15.0, float)

    # How long to wait for the Discord bot to connect before giving up (seconds)
    DISCORD_READY_TIMEOUT_SECONDS = _env_number('DISCORD_READY_TIMEOUT_SECONDS', 30.0, float)

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

    def __init__(self):
        if self.CHECK_INTERVAL_MINUTES <= 0:
            raise ConfigError(
                f"CHECK_INTERVAL_MINUTES must be positive, got {self.CHECK_INTERVAL_MINUTES}"
            )
        if self.DISCORD_BOT_TOKEN and not self.DISCORD_CHANNEL_ID:
            logger.warning(
                "DISCORD_BOT_TOKEN is set but DISCORD_CHANNEL_ID is missing; "
                "notifications will fail until it is configured"
            )
