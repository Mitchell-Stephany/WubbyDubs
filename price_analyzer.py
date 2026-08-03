from typing import Dict, List, Optional
from database import Database
from ebay_api import eBayAPI
from config import Config

class PriceAnalyzer:
    """Analyzes price changes and calculates profit potential"""
    
    def __init__(self, config: Config, database: Database, ebay_api: eBayAPI):
        self.config = config
        self.db = database
        self.ebay = ebay_api
    
    def analyze_price_change(self, product_id: str, current_price: float) -> Optional[Dict]:
        """Analyze a price change for a product"""
        # Get previous price
        previous_price = self.db.get_previous_price(product_id)
        
        if not previous_price:
            # First time seeing this product, just record the price
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
        
        # Check eBay prices
        product_name = product['name']
        ebay_price = self.ebay.get_average_price(product_name)
        
        # Calculate profit potential
        profit_info = {}
        if ebay_price:
            profit_info = self.ebay.calculate_potential_profit(current_price, ebay_price)
        
        # Determine if this is a good deal
        is_good_deal = False
        if profit_info.get('profitable', False):
            is_good_deal = True
        elif drop_percentage >= 30:  # Also alert on large drops even if not profitable
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
            'ebay_price': ebay_price,
            'potential_profit': profit_info.get('profit', 0),
            'profit_percentage': profit_info.get('profit_percentage', 0),
            'is_good_deal': is_good_deal,
            'timestamp': None  # Will be set when recording
        }
        
        # Record the deal in database
        if is_good_deal:
            self.db.record_deal(
                product_id=product_id,
                original_price=previous_price,
                new_price=current_price,
                drop_percentage=drop_percentage,
                ebay_price=ebay_price,
                potential_profit=profit_info.get('profit', 0),
                profit_percentage=profit_info.get('profit_percentage', 0)
            )
        
        return deal_info if is_good_deal else None
    
    def analyze_all_products(self) -> List[Dict]:
        """Analyze all tracked products for price changes"""
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
