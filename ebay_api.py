from typing import Dict, Optional, List
import requests
from ebaysdk.finding import Connection as Finding
from ebaysdk.exception import ConnectionError as EbayConnectionError

class eBayAPI:
    """eBay API for price comparison"""
    
    def __init__(self, config):
        self.config = config
        self.app_id = config.EBAY_APP_ID
        self.cert_id = config.EBAY_CERT_ID
        self.dev_id = config.EBAY_DEV_ID
        
        self.api = Finding(
            domain='svcs.ebay.com',
            appid=self.app_id,
            config_file=None
        )
    
    def get_average_price(self, query: str, category: str = None) -> Optional[float]:
        """Get average sold price for a product on eBay"""
        try:
            response = self.api.execute(
                'findCompletedItems',
                {
                    'keywords': query,
                    'itemFilter': [
                        {'name': 'SoldItemsOnly', 'value': 'true'},
                        {'name': 'Condition', 'value': 'New'}
                    ],
                    'paginationInput': {
                        'entriesPerPage': 50
                    }
                }
            )
            
            items = response.dict().get('searchResult', {}).get('item', [])
            
            if not items:
                return None
            
            # Calculate average sold price
            total_price = 0
            count = 0
            
            for item in items:
                try:
                    price = float(item.get('sellingStatus', {}).get('currentPrice', {}).get('value', 0))
                    if price > 0:
                        total_price += price
                        count += 1
                except (ValueError, TypeError):
                    continue
            
            return total_price / count if count > 0 else None
            
        except EbayConnectionError as e:
            print(f"eBay API error: {e}")
            return None
        except Exception as e:
            print(f"Error fetching eBay price: {e}")
            return None
    
    def get_sold_listings(self, query: str, limit: int = 20) -> List[Dict]:
        """Get recent sold listings for a product"""
        try:
            response = self.api.execute(
                'findCompletedItems',
                {
                    'keywords': query,
                    'itemFilter': [
                        {'name': 'SoldItemsOnly', 'value': 'true'},
                        {'name': 'Condition', 'value': 'New'}
                    ],
                    'paginationInput': {
                        'entriesPerPage': limit
                    },
                    'sortOrder': 'EndTimeSoonest'
                }
            )
            
            items = response.dict().get('searchResult', {}).get('item', [])
            
            listings = []
            for item in items:
                try:
                    listings.append({
                        'title': item.get('title', ''),
                        'price': float(item.get('sellingStatus', {}).get('currentPrice', {}).get('value', 0)),
                        'currency': item.get('sellingStatus', {}).get('currentPrice', {}).get('_currencyId', 'USD'),
                        'end_time': item.get('listingInfo', {}).get('endTime', ''),
                        'url': item.get('viewItemURL', ''),
                        'condition': item.get('condition', {}).get('conditionDisplayName', 'Unknown')
                    })
                except (ValueError, TypeError):
                    continue
            
            return listings
            
        except EbayConnectionError as e:
            print(f"eBay API error: {e}")
            return []
        except Exception as e:
            print(f"Error fetching eBay listings: {e}")
            return []
    
    def get_current_listings(self, query: str, limit: int = 20) -> List[Dict]:
        """Get current active listings for a product"""
        try:
            response = self.api.execute(
                'findItemsAdvanced',
                {
                    'keywords': query,
                    'itemFilter': [
                        {'name': 'Condition', 'value': 'New'},
                        {'name': 'ListingType', 'value': 'AuctionWithBIN'}
                    ],
                    'paginationInput': {
                        'entriesPerPage': limit
                    },
                    'sortOrder': 'PricePlusShippingLowest'
                }
            )
            
            items = response.dict().get('searchResult', {}).get('item', [])
            
            listings = []
            for item in items:
                try:
                    listings.append({
                        'title': item.get('title', ''),
                        'price': float(item.get('sellingStatus', {}).get('currentPrice', {}).get('value', 0)),
                        'currency': item.get('sellingStatus', {}).get('currentPrice', {}).get('_currencyId', 'USD'),
                        'url': item.get('viewItemURL', ''),
                        'condition': item.get('condition', {}).get('conditionDisplayName', 'Unknown')
                    })
                except (ValueError, TypeError):
                    continue
            
            return listings
            
        except EbayConnectionError as e:
            print(f"eBay API error: {e}")
            return []
        except Exception as e:
            print(f"Error fetching eBay listings: {e}")
            return []
    
    def calculate_potential_profit(self, retail_price: float, ebay_price: float) -> Dict:
        """Calculate potential profit after eBay fees"""
        if not ebay_price or ebay_price <= retail_price:
            return {
                'profit': 0,
                'profit_percentage': 0,
                'ebay_fee': 0,
                'profitable': False
            }
        
        # Calculate eBay fee (simplified - actual fees vary by category)
        ebay_fee = ebay_price * (self.config.EBAY_FEE_PERCENTAGE / 100)
        
        # Add estimated shipping cost (you may want to make this configurable)
        estimated_shipping = 15.0  # Average shipping cost
        
        total_cost = retail_price + ebay_fee + estimated_shipping
        profit = ebay_price - total_cost
        profit_percentage = (profit / retail_price) * 100 if retail_price > 0 else 0
        
        return {
            'profit': profit,
            'profit_percentage': profit_percentage,
            'ebay_fee': ebay_fee,
            'shipping_cost': estimated_shipping,
            'total_cost': total_cost,
            'profitable': profit > 0 and profit_percentage >= self.config.MIN_PROFIT_PERCENTAGE
        }
