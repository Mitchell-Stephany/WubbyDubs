from typing import Dict, List, Optional
from database import Database
from ebay_api import eBayAPI
from config import Config
from scrapers.ebay_sold_scraper import eBaySoldScraper

class PriceAnalyzer:
    """Analyzes price changes and calculates arbitrage profit using eBay sold listings"""
    
    def __init__(self, config: Config, database: Database, ebay_api: eBayAPI, 
                 browser_scraper=None):
        self.config = config
        self.db = database
        self.ebay = ebay_api
        self.browser_scraper = browser_scraper
        self.ebay_scraper = None
        
        # Initialize eBay sold scraper if browser scraper is available
        if browser_scraper:
            self.ebay_scraper = eBaySoldScraper(browser_scraper)
            print("eBay sold listings scraper initialized (for arbitrage profit calculation)")
    
    def analyze_price_change(self, product_id: str, current_price: float, 
                             ebay_analysis: Optional[Dict] = None) -> Optional[Dict]:
        """Analyze a price change for a product
        
        Args:
            product_id: Product ID
            current_price: Current retail price
            ebay_analysis: Pre-computed eBay analysis (optional, to avoid re-scraping)
        """
        # Get previous price
        previous_price = self.db.get_previous_price(product_id)
        
        if not previous_price:
            return None
        
        # Calculate price drop percentage
        if previous_price > 0:
            drop_percentage = ((previous_price - current_price) / previous_price) * 100
        else:
            drop_percentage = 0
        
        # Only proceed if price dropped
        if drop_percentage <= 0:
            return None
        
        # Get product info
        products = self.db.get_all_products()
        product = next((p for p in products if p['product_id'] == product_id), None)
        
        if not product:
            return None
        
        # Get eBay pricing data
        ebay_price = None
        profit_info = {}
        
        if ebay_analysis:
            # Use pre-computed analysis
            ebay_price = ebay_analysis.get('estimated_ebay_price')
            profit_info = ebay_analysis
        elif self.ebay_scraper:
            # Will be computed asynchronously elsewhere
            profit_info = {
                'profit': 0,
                'profit_percentage': 0,
                'requires_ebay': True
            }
        elif self.ebay.enabled:
            # Use eBay API if available
            product_name = product['name']
            ebay_price = self.ebay.get_average_price(product_name)
            if ebay_price:
                profit_info = self.ebay.calculate_potential_profit(current_price, ebay_price)
            else:
                profit_info = {
                    'profit': 0,
                    'profit_percentage': 0,
                    'requires_ebay': True
                }
        else:
            # Fallback mode: no eBay data
            profit_info = {
                'profit': 0,
                'profit_percentage': 0,
                'requires_ebay': True
            }
        
        # Determine if this is a good deal
        is_good_deal = False
        
        if profit_info.get('is_profitable', False):
            # Profitable arbitrage opportunity
            is_good_deal = True
        elif drop_percentage >= self.config.MIN_PROFIT_PERCENTAGE:
            # Large price drop even without eBay data
            is_good_deal = True
        
        deal_info = {
            'product_id': product_id,
            'name': product['name'],
            'retailer': product['retailer'],
            'url': product['url'],
            'category': product['category'],
            'original_price': previous_price,
            'new_price': current_price,
            'drop_percentage': drop_percentage,
            'ebay_price': ebay_price or profit_info.get('estimated_ebay_price'),
            'ebay_price_range': profit_info.get('ebay_price_range'),
            'potential_profit': profit_info.get('profit', 0),
            'profit_percentage': profit_info.get('profit_percentage', 0),
            'roi': profit_info.get('roi', 0),
            'ebay_confidence': profit_info.get('ebay_confidence'),
            'sample_size': profit_info.get('sample_size'),
            'is_good_deal': is_good_deal,
            'is_arbitrage': profit_info.get('is_profitable', False),
            'fallback_mode': not profit_info.get('is_profitable', False) and not ebay_price,
            'timestamp': None
        }
        
        # Record the deal in database
        if is_good_deal:
            self.db.record_deal(
                product_id=product_id,
                original_price=previous_price,
                new_price=current_price,
                drop_percentage=drop_percentage,
                ebay_price=ebay_price or profit_info.get('estimated_ebay_price'),
                potential_profit=profit_info.get('profit', 0),
                profit_percentage=profit_info.get('profit_percentage', 0)
            )
        
        return deal_info if is_good_deal else None
    
    def analyze_all_products(self) -> List[Dict]:
        """Analyze all tracked products for price changes (synchronous, no eBay scraping)"""
        products = self.db.get_all_products()
        deals = []
        
        for product in products:
            product_id = product['product_id']
            current_price = self.db.get_latest_price(product_id)
            
            if current_price:
                deal = self.analyze_price_change(product_id, current_price)
                if deal:
                    deals.append(deal)
        
        return deals
    
    async def analyze_all_products_with_ebay(self) -> List[Dict]:
        """Analyze all products with eBay arbitrage calculation (async)"""
        products = self.db.get_all_products()
        deals = []
        
        for product in products:
            product_id = product['product_id']
            current_price = self.db.get_latest_price(product_id)
            
            if not current_price or current_price <= 0:
                continue
            
            # Check if price dropped
            previous_price = self.db.get_previous_price(product_id)
            if not previous_price or previous_price <= current_price:
                continue
            
            # Get eBay analysis
            ebay_analysis = None
            if self.ebay_scraper:
                try:
                    print(f"    Checking eBay prices for: {product['name'][:40]}...")
                    ebay_analysis = await self.ebay_scraper.calculate_arbitrage_profit(
                        product['name'],
                        current_price,
                        self.config.EBAY_FEE_PERCENTAGE
                    )
                    if ebay_analysis:
                        print(f"    eBay: ${ebay_analysis['estimated_ebay_price']:.2f} "
                              f"(profit: ${ebay_analysis['profit']:.2f}, "
                              f"confidence: {ebay_analysis['ebay_confidence']})")
                    await asyncio.sleep(2)  # Rate limiting
                except Exception as e:
                    print(f"    eBay analysis error: {e}")
            
            deal = self.analyze_price_change(product_id, current_price, ebay_analysis)
            if deal:
                deals.append(deal)
        
        return deals
    
    def get_significant_drops(self, min_drop_percentage: float = 20) -> List[Dict]:
        """Get products with significant price drops"""
        products = self.db.get_all_products()
        significant_drops = []
        
        for product in products:
            product_id = product['product_id']
            current_price = self.db.get_latest_price(product_id)
            previous_price = self.db.get_previous_price(product_id)
            
            if current_price and previous_price and previous_price > 0:
                drop_percentage = ((previous_price - current_price) / previous_price) * 100
                
                if drop_percentage >= min_drop_percentage:
                    significant_drops.append({
                        'product_id': product_id,
                        'name': product['name'],
                        'retailer': product['retailer'],
                        'url': product['url'],
                        'original_price': previous_price,
                        'new_price': current_price,
                        'drop_percentage': drop_percentage
                    })
        
        return significant_drops


# Need asyncio import for the async method
import asyncio
