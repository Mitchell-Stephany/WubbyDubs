from typing import Dict, Optional, List
from ebaysdk.finding import Connection as Finding
from ebaysdk.exception import ConnectionError as EbayConnectionError

class eBayAPI:
    """eBay API for price comparison"""
    
    NEW_SOLD_FILTERS = [
        {'name': 'SoldItemsOnly', 'value': 'true'},
        {'name': 'Condition', 'value': 'New'}
    ]
    
    ESTIMATED_SHIPPING = 15.0  # Average shipping cost
    
    def __init__(self, config):
        self.config = config
        self.app_id = config.EBAY_APP_ID
        self.cert_id = config.EBAY_CERT_ID
        self.dev_id = config.EBAY_DEV_ID
        self.enabled = config.EBAY_ENABLED
        
        if self.enabled:
            try:
                self.api = Finding(
                    domain='svcs.ebay.com',
                    appid=self.app_id,
                    config_file=None
                )
            except Exception as e:
                print(f"Failed to initialize eBay API: {e}")
                self.enabled = False
        else:
            print("eBay API not configured - running in fallback mode")
            self.api = None
    
    def _find_items(self, operation: str, params: Dict, error_message: str) -> Optional[List[Dict]]:
        """Run a Finding API operation and return the matched items"""
        if not self.enabled:
            return None
        
        try:
            response = self.api.execute(operation, params)
            return response.dict().get('searchResult', {}).get('item', [])
        except EbayConnectionError as e:
            print(f"eBay API error: {e}")
        except Exception as e:
            print(f"{error_message}: {e}")
        return None
    
    @staticmethod
    def _item_price(item: Dict) -> float:
        """Current price of a listing"""
        return float(item.get('sellingStatus', {}).get('currentPrice', {}).get('value', 0))
    
    @classmethod
    def _to_listing(cls, item: Dict, with_end_time: bool) -> Dict:
        """Convert an API item into a listing dictionary"""
        listing = {
            'title': item.get('title', ''),
            'price': cls._item_price(item),
            'currency': item.get('sellingStatus', {}).get('currentPrice', {}).get('_currencyId', 'USD'),
            'url': item.get('viewItemURL', ''),
            'condition': item.get('condition', {}).get('conditionDisplayName', 'Unknown')
        }
        
        if with_end_time:
            listing['end_time'] = item.get('listingInfo', {}).get('endTime', '')
        
        return listing
    
    @classmethod
    def _to_listings(cls, items: List[Dict], with_end_time: bool = False) -> List[Dict]:
        """Convert API items into listing dictionaries, skipping malformed ones"""
        listings = []
        for item in items:
            try:
                listings.append(cls._to_listing(item, with_end_time))
            except (ValueError, TypeError):
                continue
        return listings
    
    def get_average_price(self, query: str, category: str = None) -> Optional[float]:
        """Get average sold price for a product on eBay"""
        # Fallback: return None (system will use price drop percentage instead)
        items = self._find_items(
            'findCompletedItems',
            {
                'keywords': query,
                'itemFilter': self.NEW_SOLD_FILTERS,
                'paginationInput': {'entriesPerPage': 50}
            },
            "Error fetching eBay price"
        )
        
        if not items:
            return None
        
        # Calculate average sold price
        prices = []
        for item in items:
            try:
                price = self._item_price(item)
            except (ValueError, TypeError):
                continue
            if price > 0:
                prices.append(price)
        
        return sum(prices) / len(prices) if prices else None
    
    def get_sold_listings(self, query: str, limit: int = 20) -> List[Dict]:
        """Get recent sold listings for a product"""
        items = self._find_items(
            'findCompletedItems',
            {
                'keywords': query,
                'itemFilter': self.NEW_SOLD_FILTERS,
                'paginationInput': {'entriesPerPage': limit},
                'sortOrder': 'EndTimeSoonest'
            },
            "Error fetching eBay listings"
        )
        
        return self._to_listings(items, with_end_time=True) if items else []
    
    def get_current_listings(self, query: str, limit: int = 20) -> List[Dict]:
        """Get current active listings for a product"""
        items = self._find_items(
            'findItemsAdvanced',
            {
                'keywords': query,
                'itemFilter': [
                    {'name': 'Condition', 'value': 'New'},
                    {'name': 'ListingType', 'value': 'AuctionWithBIN'}
                ],
                'paginationInput': {'entriesPerPage': limit},
                'sortOrder': 'PricePlusShippingLowest'
            },
            "Error fetching eBay listings"
        )
        
        return self._to_listings(items) if items else []
    
    def calculate_potential_profit(self, retail_price: float, ebay_price: float) -> Dict:
        """Calculate potential profit after eBay fees"""
        if not self.enabled or not ebay_price or ebay_price <= retail_price:
            return {
                'profit': 0,
                'profit_percentage': 0,
                'ebay_fee': 0,
                'profitable': False,
                'requires_ebay': True
            }
        
        # Calculate eBay fee (simplified - actual fees vary by category)
        ebay_fee = ebay_price * (self.config.EBAY_FEE_PERCENTAGE / 100)
        
        # Add estimated shipping cost (you may want to make this configurable)
        estimated_shipping = self.ESTIMATED_SHIPPING
        
        total_cost = retail_price + ebay_fee + estimated_shipping
        profit = ebay_price - total_cost
        profit_percentage = (profit / retail_price) * 100 if retail_price > 0 else 0
        
        return {
            'profit': profit,
            'profit_percentage': profit_percentage,
            'ebay_fee': ebay_fee,
            'shipping_cost': estimated_shipping,
            'total_cost': total_cost,
            'profitable': profit > 0 and profit_percentage >= self.config.MIN_PROFIT_PERCENTAGE,
            'requires_ebay': False
        }
