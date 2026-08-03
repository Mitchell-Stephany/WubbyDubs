import logging
from typing import Dict, Optional, List
import requests
from bs4 import BeautifulSoup
from exceptions import ScraperError
from .base import BaseScraper

logger = logging.getLogger(__name__)

class HomeDepotScraper(BaseScraper):
    """Home Depot web scraper"""
    
    BASE_URL = "https://www.homedepot.com"
    
    def __init__(self, config):
        super().__init__(config)

    def _get_soup(self, url: str, params: Dict = None) -> BeautifulSoup:
        """Fetch a page, raising ScraperError when the request fails."""
        try:
            response = self._get(url, params=params)
        except requests.RequestException as exc:
            raise ScraperError(f"Home Depot request to {url} failed: {exc}") from exc
        return BeautifulSoup(response.text, 'lxml')

    @staticmethod
    def _parse_price(price_text: str) -> Optional[float]:
        try:
            return float(price_text.replace('$', '').replace(',', '').strip())
        except ValueError:
            return None

    def get_product_price(self, product_id: str) -> Optional[float]:
        """Get current price for a product using product ID"""
        url = f"{self.BASE_URL}/p/{product_id}"
        soup = self._get_soup(url)

        # Home Depot price selectors
        price_selectors = [
            '[data-testid="product-price"]',
            '.price__format',
            '.price-dollars',
            '.price-cents',
            '.product-price'
        ]

        for selector in price_selectors:
            price_element = soup.select_one(selector)
            if price_element:
                price = self._parse_price(price_element.get_text())
                if price is not None:
                    return price

        logger.warning("No parseable price found on Home Depot page for %s", product_id)
        return None

    def get_product_info(self, product_id: str) -> Dict:
        """Get detailed product information"""
        url = f"{self.BASE_URL}/p/{product_id}"
        soup = self._get_soup(url)

        # Extract product name
        name_element = soup.select_one('h1.product-title')
        name = name_element.get_text().strip() if name_element else "Unknown"

        # Extract price
        price = self.get_product_price(product_id)

        # Extract category from breadcrumb
        category_elements = soup.select('.breadcrumb a')
        category = category_elements[-1].get_text().strip() if category_elements else "Unknown"

        return {
            'name': name,
            'url': url,
            'category': category,
            'price': price,
            'description': ''
        }

    def search_products(self, query: str, category: str = None) -> List[Dict]:
        """Search for products on Home Depot"""
        url = f"{self.BASE_URL}/s/{query}"
        params = {
            'NCNI-5': '1',
            'Nao-': '1',
        }

        if category:
            params['M'] = category

        soup = self._get_soup(url, params=params)
        products = []

        # Home Depot product cards
        product_cards = soup.select('.product-pod')
        skipped = 0

        for card in product_cards[:20]:  # Limit to 20 results
            # Extract product ID from URL
            link_element = card.select_one('a.product-pod__link')
            product_url = link_element.get('href') if link_element else None
            if not product_url or '/p/' not in product_url:
                skipped += 1
                continue

            product_id = product_url.split('/p/')[-1].split('/')[0]

            # Extract name
            name_element = card.select_one('.product-pod__title')
            name = name_element.get_text().strip() if name_element else "Unknown"

            # Extract price
            price_element = card.select_one('.price__format')
            price = self._parse_price(price_element.get_text()) if price_element else None

            products.append({
                'product_id': product_id,
                'name': name,
                'url': f"{self.BASE_URL}{product_url}",
                'category': category or 'Unknown',
                'price': price,
                'retailer': 'homedepot'
            })

        if skipped:
            logger.warning("Skipped %s Home Depot result cards without a product link", skipped)
        if product_cards and not products:
            raise ScraperError(
                f"Home Depot returned {len(product_cards)} cards for {query!r} but none could be parsed"
            )

        return products

    def get_trending_products(self, category: str = 'all') -> List[Dict]:
        """Get trending products from Home Depot"""
        # Home Depot doesn't have a public trending API
        popular_searches = [
            'tools', 'appliances', 'kitchen', 'bathroom', 
            'lighting', 'flooring', 'paint', 'lawn'
        ]
        
        search_term = category if category != 'all' else popular_searches[0]
        return self.search_products(search_term, category)
