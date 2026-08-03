from typing import Dict, Optional, List
from .base import BaseScraper
from utils import build_product_record, parse_price, pick_search_term

class TargetScraper(BaseScraper):
    """Target web scraper"""
    
    BASE_URL = "https://www.target.com"
    
    PRICE_SELECTORS = [
        '[data-test="product-price"]',
        '.Price-characteristic',
        '.style__PriceText___2HiQw',
        'span[data-test="product-price"]'
    ]
    
    POPULAR_SEARCHES = [
        'electronics', 'home goods', 'kitchen', 'furniture',
        'toys', 'beauty', 'clothing', 'appliances'
    ]
    
    def __init__(self, config):
        super().__init__(config)
    
    def get_product_price(self, product_id: str) -> Optional[float]:
        """Get current price for a product using TCIN (Target ID)"""
        try:
            soup = self._get_soup(f"{self.BASE_URL}/p/{product_id}")
            return self._select_price(soup, self.PRICE_SELECTORS)
        except Exception as e:
            print(f"Error fetching Target price for {product_id}: {e}")
        return None
    
    def get_product_info(self, product_id: str) -> Dict:
        """Get detailed product information"""
        try:
            url = f"{self.BASE_URL}/p/{product_id}"
            soup = self._get_soup(url)
            
            return {
                'name': self._select_text(soup, '[data-test="product-title"]', "Unknown"),
                'url': url,
                'category': self._select_breadcrumb_category(soup, '[data-test="breadcrumb"] a'),
                'price': self.get_product_price(product_id),
                'description': ''
            }
            
        except Exception as e:
            print(f"Error fetching Target product info for {product_id}: {e}")
        return {}
    
    def search_products(self, query: str, category: str = None) -> List[Dict]:
        """Search for products on Target"""
        try:
            params = {
                'searchTerm': query,
                'category': category,
                'sortName': 'bestselling'
            }
            
            soup = self._get_soup(f"{self.BASE_URL}/s", params=params)
            products = []
            
            # Target product cards
            product_cards = soup.select('[data-test="product-card"]')
            
            for card in product_cards[:20]:  # Limit to 20 results
                try:
                    # Extract TCIN from data attribute
                    tcin = card.get('data-tcin')
                    if not tcin:
                        continue
                    
                    link_element = card.select_one('a[href*="/p/"]')
                    product_url = f"{self.BASE_URL}{link_element['href']}" if link_element else f"{self.BASE_URL}/p/{tcin}"
                    
                    products.append(build_product_record(
                        product_id=tcin,
                        name=self._select_text(card, '[data-test="product-title"]', "Unknown"),
                        url=product_url,
                        category=category,
                        price=parse_price(self._select_text(card, '[data-test="product-price"]')),
                        retailer='target'
                    ))
                    
                except Exception as e:
                    print(f"Error parsing Target product card: {e}")
                    continue
            
            return products
            
        except Exception as e:
            print(f"Error searching Target products: {e}")
        return []
    
    def get_trending_products(self, category: str = 'all') -> List[Dict]:
        """Get trending products from Target"""
        # Target doesn't have a public trending API, so we'll search popular terms
        return self.search_products(pick_search_term(category, self.POPULAR_SEARCHES), category)
