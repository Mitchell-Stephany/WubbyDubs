# Price Arbitrage Tracker

A Python-based system that tracks pricing data from major retailers (Best Buy, Target, Home Depot) and identifies profitable arbitrage opportunities by comparing prices against eBay listings. The system sends Discord notifications when it finds deals with profit potential.

## Features

- **Multi-Retailer Tracking**: Supports Best Buy (API), Target (web scraping), Home Depot (web scraping)
- **Real-Time Price Monitoring**: Configurable check intervals (default: 5 minutes)
- **eBay Price Comparison**: Uses eBay API to compare retail prices against market value (optional)
- **Fallback Mode**: Works without eBay API by alerting on significant price drops
- **Profit Calculation**: Automatically calculates potential profit after eBay fees and shipping costs
- **Discord Notifications**: Real-time alerts for profitable deals
- **Trend Discovery**: Automatically discovers trending products to track
- **Price History**: SQLite database stores complete price history for analysis

## Prerequisites

- Python 3.8+
- Discord Bot Token
- eBay API credentials (App ID, Cert ID, Dev ID)
- Best Buy API Key (optional, for Best Buy API access)

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Environment Variables

Copy `.env.example` to `.env` and fill in your credentials:

```bash
cp .env.example .env
```

Edit `.env` with your values:

```env
# Discord Bot Configuration (Required)
DISCORD_BOT_TOKEN=your_discord_bot_token_here
DISCORD_CHANNEL_ID=your_channel_id_here

# eBay API Configuration (Optional - for profit calculations)
EBAY_APP_ID=your_ebay_app_id_here
EBAY_CERT_ID=your_ebay_cert_id_here
EBAY_DEV_ID=your_ebay_dev_id_here

# Best Buy API Configuration (Optional - for Best Buy API access)
BEST_BUY_API_KEY=your_best_buy_api_key_here

# Configuration
CHECK_INTERVAL_MINUTES=5
MIN_PROFIT_PERCENTAGE=15
EBAY_FEE_PERCENTAGE=13
```

**Note**: The system works without eBay API by using price drop percentage as the alert threshold. With eBay API, it calculates actual profit potential.

### 3. Get API Credentials

#### Discord Bot
1. Go to Discord Developer Portal
2. Create a new application
3. Create a bot user
4. Copy the bot token
5. Invite the bot to your server with appropriate permissions
6. Get the channel ID where you want notifications

#### eBay API
1. Go to eBay Developers Portal
2. Create an application
3. Get your App ID, Cert ID, and Dev ID
4. Note: eBay API has rate limits

#### Best Buy API (Optional)
1. Go to Best Buy Developer Portal
2. Sign up for API access
3. Get your API key
4. Note: Without this, Best Buy scraping will use web scraping

## Usage

### Start the Tracker

```bash
python main.py
```

The system will:
1. Start the Discord bot
2. Discover trending products to track
3. Begin checking prices at the configured interval
4. Send notifications when profitable deals are found

### How It Works

**With eBay API:**
1. **Product Discovery**: The system automatically discovers trending products from supported retailers
2. **Price Monitoring**: Checks prices every 5 minutes (configurable)
3. **Price Comparison**: Compares retail prices against eBay sold listings
4. **Profit Calculation**: Calculates potential profit after:
   - eBay fees (default 13%)
   - Estimated shipping costs ($15 default)
   - Retail price
5. **Notifications**: Sends Discord alerts when profit percentage exceeds minimum threshold (default 15%)

**Without eBay API (Fallback Mode):**
1. **Product Discovery**: Discovers trending products from supported retailers
2. **Price Monitoring**: Checks prices every 5 minutes (configurable)
3. **Price Drop Detection**: Monitors for significant price drops
4. **Notifications**: Sends Discord alerts when price drop exceeds minimum threshold (default 15%)

## Tests

Unit tests live in `tests/` and run fully offline (no network, no browser, no Discord connection):

```bash
pip install -r requirements-dev.txt
pytest
pytest --cov=. --cov-report=term-missing   # with coverage
```

The `test_*.py` scripts in the repository root are manual smoke scripts that hit live retailer and
Discord endpoints; they are excluded from the default `pytest` run via `pytest.ini`.

## Configuration

### Check Interval
Adjust how often prices are checked:
```env
CHECK_INTERVAL_MINUTES=5
```

### Profit Threshold
Minimum profit percentage to trigger alerts:
```env
MIN_PROFIT_PERCENTAGE=15
```

### eBay Fee Percentage
Adjust eBay fee calculation:
```env
EBAY_FEE_PERCENTAGE=13
```

## Architecture

- **`main.py`**: Main application loop and scheduler
- **`config.py`**: Configuration management
- **`database.py`**: SQLite database operations
- **`scrapers/`**: Retailer-specific scrapers
  - `base.py`: Base scraper class
  - `bestbuy.py`: Best Buy API scraper
  - `target.py`: Target web scraper
  - `homedepot.py`: Home Depot web scraper
- **`ebay_api.py`**: eBay API integration
- **`discord_bot.py`**: Discord notification system
- **`price_analyzer.py`**: Price change analysis and profit calculation
- **`trend_discovery.py`**: Trending product discovery

## Database

The system uses SQLite (`price_tracker.db`) with three main tables:

- **products**: Tracked products and their metadata
- **price_history**: Historical price data
- **deals**: Discovered profitable deals

## Troubleshooting

### Discord Bot Not Connecting
- Verify your bot token is correct
- Ensure the bot has permissions for the channel
- Check that the channel ID is correct

### eBay API Errors
- Verify your API credentials
- Check if you've hit rate limits
- Ensure your application is properly configured

### Scraping Issues
- Some retailers may block scraping - consider using proxies
- Respect rate limits to avoid being blocked
- API access (when available) is more reliable than scraping

## Legal and Ethical Considerations

- Respect retailers' terms of service
- Don't overload servers with too many requests
- Be aware that arbitrage opportunities may be limited by retailer policies
- This tool is for educational purposes - actual profit depends on many factors

## Future Enhancements

- Add more retailers (Walmart, Amazon, etc.)
- Implement machine learning for better trend prediction
- Add web dashboard for monitoring
- Support for multiple Discord channels
- Advanced filtering and custom alerts
- Historical price analysis and charts

## Disclaimer

This software is provided as-is for educational purposes. Actual profit potential varies based on market conditions, fees, shipping costs, and other factors. Always verify deals independently before making purchasing decisions.
