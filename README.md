# Price Arbitrage Tracker

A Python-based system that scrapes real product data from Amazon, Walmart, and Target, monitors prices, and calculates arbitrage profit potential by comparing against eBay resale values. Sends Discord notifications when profitable deals are found.

## How It Works

1. **Product Discovery** - Searches Amazon, Walmart, and Target for products across 119 search terms in 7 categories (electronics, gaming, home appliances, tools, outdoor, fitness, beauty/health). Terms are rotated randomly each cycle to avoid repetition.

2. **Price Monitoring** - Visits each tracked product's page directly to check the current price every 30 minutes.

3. **eBay Arbitrage Calculation** - When a price drop is detected, scrapes eBay listing prices for that product to estimate resale value, then calculates profit after eBay fees (13%).

4. **Discord Notifications** - Sends a formatted alert to your Discord channel when a profitable arbitrage opportunity is found, including:
   - Product name and retailer
   - Price drop (old vs new price)
   - Estimated eBay sale price (with range and confidence level)
   - Estimated profit after fees
   - Direct link to buy the product

## Retailers

| Retailer | Status | Method |
|----------|--------|--------|
| Amazon | Working | Chromium browser (Playwright) |
| Walmart | Working | Chromium browser (Playwright) |
| Target | Working | Firefox browser (Playwright) |
| Home Depot | Blocked | Anti-bot detection (403) |
| Lowe's | Blocked | Anti-bot detection (403) |

The system uses Playwright with stealth mode (anti-detection scripts) to bypass bot protection. Firefox is used for Target because Chromium gets blocked.

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
python -m playwright install chromium
python -m playwright install firefox
```

### 2. Configure Environment

Copy `.env.example` to `.env` and fill in your Discord credentials:

```bash
cp .env.example .env
```

```env
DISCORD_BOT_TOKEN=your_discord_bot_token_here
DISCORD_CHANNEL_ID=your_discord_channel_id_here
CHECK_INTERVAL_MINUTES=30
MIN_PROFIT_PERCENTAGE=15
EBAY_FEE_PERCENTAGE=13
```

### 3. Get Discord Bot Token

1. Go to [Discord Developer Portal](https://discord.com/developers/applications)
2. Create a new application
3. Create a bot user and copy the token
4. Invite the bot to your server
5. Get the channel ID where you want notifications (right-click channel > Copy ID)

### 4. Run

```bash
python main.py
```

Leave it running. It will:
- Immediately discover products from 5 random search terms
- Check prices every 30 minutes
- Discover new products every 2 hours
- Send Discord alerts for profitable deals

Press `Ctrl+C` to stop.

## Schedule

| Task | Interval | Description |
|------|----------|-------------|
| Product discovery | Every 2 hours | Searches 5 random terms across Amazon/Walmart/Target |
| Price check | Every 30 min | Visits each tracked product's page directly |
| Arbitrage analysis | Every 30 min | Scrapes eBay prices for products with price drops |
| Discord notification | On demand | Sent when a profitable deal is found |

## Project Structure

```
price-arbitrage-tracker/
├── main.py                  # Main application - scheduler and run loop
├── config.py                # Configuration from environment variables
├── database.py              # SQLite database operations
├── discord_bot.py           # Discord notification system
├── price_analyzer.py        # Price drop analysis and eBay arbitrage calculation
├── ebay_api.py              # eBay API wrapper (optional, disabled by default)
├── search_terms.py          # 119 product search terms across 7 categories
├── scrapers/
│   ├── __init__.py          # Package exports
│   ├── browser_scraper.py   # Playwright browser scraper (Amazon, Walmart, Target)
│   └── ebay_sold_scraper.py # eBay listing scraper for resale value estimation
├── test_e2e.py              # End-to-end system test
├── test_ebay.py             # eBay scraper test
├── requirements.txt         # Python dependencies
└── .env.example             # Environment variable template
```

## Database

SQLite (`price_tracker.db`) with three tables:

- **products** - Tracked products (ID, retailer, name, URL, category)
- **price_history** - Historical price records per product
- **deals** - Discovered deals with profit calculations

## Testing

```bash
# Full end-to-end test (discovers products, simulates price drops, checks eBay)
python test_e2e.py

# Test eBay scraper only
python test_ebay.py
```

## Notes

- Home Depot and Lowe's block all scraping attempts (403 errors) even with browser automation. They are skipped.
- eBay sold listings require login, so the system scrapes active listings and applies a 10% discount to estimate sold prices.
- The system uses random delays (3-10 seconds) between requests to avoid rate limiting.
- Prices are extracted from product pages directly (1 page load per product) rather than re-searching, to minimize scraping load.

## Disclaimer

This software is for educational purposes. Actual profit depends on market conditions, shipping costs, item condition, and other factors. Always verify deals independently before purchasing.
