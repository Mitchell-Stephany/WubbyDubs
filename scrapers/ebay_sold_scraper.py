"""
eBay Sold Listings Scraper - estimates resale value by scraping completed/sold listings.
Uses Playwright (Chromium) to bypass eBay's bot detection.

Note: eBay requires login for sold listings filter, so we scrape active listings
and use those prices as a proxy for market value (slightly conservative estimate).
"""

import asyncio
import re
import statistics
from typing import Optional, List, Dict


class eBaySoldScraper:
    """Scrapes eBay listings to estimate resale value of a product"""
    
    def __init__(self, browser_scraper):
        """
        Args:
            browser_scraper: BrowserScraper instance to reuse its browser
        """
        self.browser_scraper = browser_scraper
    
    async def get_listing_prices(self, product_name: str, limit: int = 15) -> List[float]:
        """
        Scrape eBay listings for a product and return list of prices.
        Uses active listings as a proxy for market value (slightly conservative).
        
        Args:
            product_name: Product name to search for
            limit: Max number of prices to collect
            
        Returns:
            List of prices (floats)
        """
        prices = []
        
        try:
            # Use Chromium for eBay (works better than Firefox)
            page = await self.browser_scraper._get_page(browser_type='chromium')
            
            # First go to eBay homepage to establish session
            await page.goto('https://www.ebay.com', wait_until='domcontentloaded', timeout=30000)
            await asyncio.sleep(2)
            
            # eBay search URL (sorted by lowest price)
            query = product_name.replace(' ', '+')[:80]
            url = f"https://www.ebay.com/sch/i.html?_nkw={query}&_sop=15"  # _sop=15 = price lowest first
            
            print(f"    [eBay] Searching listings for '{product_name[:40]}...'")
            response = await page.goto(url, wait_until='domcontentloaded', timeout=30000)
            
            if not response or response.status != 200:
                print(f"    [eBay] Navigation failed (status: {response.status if response else 'N/A'})")
                await page.close()
                return []
            
            # Wait for results to render
            await asyncio.sleep(5)
            await page.evaluate('window.scrollTo(0, 500)')
            await asyncio.sleep(2)
            
            # Extract prices - eBay's new structure uses su-styled-text and s-card classes
            prices = await page.evaluate('''(limit) => {
                const prices = [];
                
                // Method 1: New eBay structure - su-card containers
                const cards = document.querySelectorAll('[class*="su-card"], [class*="s-card"]');
                for (const card of cards) {
                    if (prices.length >= limit) break;
                    
                    // Find price element
                    const priceEls = card.querySelectorAll('span, div');
                    for (const el of priceEls) {
                        const text = el.textContent.trim();
                        const match = text.match(/^\\$([\\d,]+\\.?\\d*)$/);
                        if (match) {
                            const price = parseFloat(match[1].replace(',', ''));
                            if (price > 0 && price < 100000) {
                                prices.push(price);
                                break;
                            }
                        }
                    }
                }
                
                // Method 2: Old structure - s-item
                if (prices.length === 0) {
                    const items = document.querySelectorAll('.s-item, li.s-item');
                    for (const item of items) {
                        if (prices.length >= limit) break;
                        const titleEl = item.querySelector('.s-item__title, h3.s-item__title');
                        if (!titleEl) continue;
                        const title = titleEl.textContent.trim();
                        if (title.includes('Shop on eBay') || title.startsWith('results for')) continue;
                        
                        const priceEl = item.querySelector('.s-item__price, span.s-item__price');
                        if (priceEl) {
                            const match = priceEl.textContent.match(/\\$([\\d,]+\\.?\\d*)/);
                            if (match) {
                                const price = parseFloat(match[1].replace(',', ''));
                                if (price > 0 && price < 100000) {
                                    prices.push(price);
                                }
                            }
                        }
                    }
                }
                
                // Method 3: Fallback - find all price-like elements
                if (prices.length === 0) {
                    const allEls = document.querySelectorAll('span.su-styled-text, span[class*="price"]');
                    for (const el of allEls) {
                        if (prices.length >= limit) break;
                        const text = el.textContent.trim();
                        const match = text.match(/^\\$([\\d,]+\\.?\\d*)$/);
                        if (match) {
                            const price = parseFloat(match[1].replace(',', ''));
                            if (price > 0 && price < 100000) {
                                prices.push(price);
                            }
                        }
                    }
                }
                
                return prices;
            }''', limit)
            
            await page.close()
            print(f"    [eBay] Found {len(prices)} listing prices")
            return prices
            
        except Exception as e:
            print(f"    [eBay] Search error: {e}")
            return []
    
    async def get_estimated_resale_value(self, product_name: str) -> Optional[Dict]:
        """
        Get estimated resale value for a product based on eBay listings.
        
        Note: Uses active listing prices, which tend to be slightly higher than
        sold prices. We apply a 10% discount to estimate actual sold prices.
        
        Returns:
            Dict with:
                - median_price: Median price (best estimate)
                - mean_price: Average price
                - min_price: Lowest price
                - max_price: Highest price
                - sample_size: Number of listings found
                - confidence: 'high' (10+), 'medium' (5+), 'low' (3+), 'very_low' (<3)
        """
        prices = await self.get_listing_prices(product_name, limit=15)
        
        if not prices:
            return None
        
        # Sort prices and remove extreme outliers (keep middle 80%)
        prices.sort()
        if len(prices) >= 5:
            # Remove lowest 10% and highest 10%
            trim_count = max(1, len(prices) // 10)
            trimmed = prices[trim_count:-trim_count]
        else:
            trimmed = prices
        
        # Apply 10% discount to estimate sold prices (active listings tend to be higher)
        adjusted_prices = [p * 0.9 for p in trimmed]
        
        sample_size = len(adjusted_prices)
        
        # Confidence based on sample size
        if sample_size >= 10:
            confidence = 'high'
        elif sample_size >= 5:
            confidence = 'medium'
        elif sample_size >= 3:
            confidence = 'low'
        else:
            confidence = 'very_low'
        
        return {
            'median_price': statistics.median(adjusted_prices),
            'mean_price': statistics.mean(adjusted_prices),
            'min_price': min(adjusted_prices),
            'max_price': max(adjusted_prices),
            'sample_size': sample_size,
            'confidence': confidence
        }
    
    async def calculate_arbitrage_profit(self, product_name: str, retail_price: float,
                                          ebay_fee_percentage: float = 13.0) -> Optional[Dict]:
        """
        Calculate potential arbitrage profit for a product.
        
        Args:
            product_name: Name of the product
            retail_price: Current price at the retailer
            ebay_fee_percentage: eBay + PayPal fees as percentage of sale price
            
        Returns:
            Dict with profit analysis or None if no eBay data
        """
        ebay_data = await self.get_estimated_resale_value(product_name)
        
        if not ebay_data:
            return None
        
        # Use median price as the expected sale price (more robust than mean)
        estimated_sale_price = ebay_data['median_price']
        
        # Calculate fees
        fees = estimated_sale_price * (ebay_fee_percentage / 100)
        
        # Profit = sale price - retail price - fees
        profit = estimated_sale_price - retail_price - fees
        profit_percentage = (profit / retail_price * 100) if retail_price > 0 else 0
        
        # ROI = profit / cost * 100
        roi = (profit / retail_price * 100) if retail_price > 0 else 0
        
        return {
            'retail_price': retail_price,
            'estimated_ebay_price': estimated_sale_price,
            'ebay_price_range': f"${ebay_data['min_price']:.2f} - ${ebay_data['max_price']:.2f}",
            'fees': fees,
            'profit': profit,
            'profit_percentage': profit_percentage,
            'roi': roi,
            'is_profitable': profit > 0,
            'ebay_confidence': ebay_data['confidence'],
            'sample_size': ebay_data['sample_size'],
            'ebay_min': ebay_data['min_price'],
            'ebay_max': ebay_data['max_price'],
            'ebay_mean': ebay_data['mean_price'],
        }
