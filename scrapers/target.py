import logging
from typing import Dict, Optional, List
import requests
from bs4 import BeautifulSoup
from exceptions import ScraperError
from .base import BaseScraper

logger = logging.getLogger(__name__)

class TargetScraper(BaseScraper):
    """Target web scraper"""
    
    BASE_URL = "https://www.target.com"
    
    def __init__(self, config):
        super().__init__(config)

    def _get_soup(self, url: str, params: Dict = None) -> BeautifulSoup:
        """Fetch a page, raising ScraperError when the request fails."""
        try:
            response = self._get(url, params=params)
        except requests.RequestException as exc:
            raise ScraperError(f"Target request to {url} failed: {exc}") from exc
        return BeautifulSoup(response.text, 'lxml')

    @staticmethod
    def _parse_price(price_text: str) -> Optional[float]:
        try:
            return float(price_text.replace('$', '').replace(',', '').strip())
        except ValueError:
            return None

    def get_product_price(self, product_id: str) -> Optional[float]:
        """Get current price for a product using TCIN (Target ID)"""
        url = f"{self.BASE_URL}/p/{product_id}"
        soup = self._get_soup(url)

        # Try to find price in various formats Target uses
        price_selectors = [
            '[data-test="product-price"]',
            '.Price-characteristic',
            '.style__PriceText___2HiQw',
            'span[data-test="product-price"]'
        ]

        for selector in price_selectors:
            price_element = soup.select_one(selector)
            if price_element:
                price = self._parse_price(price_element.get_text())
                if price is not None:
                    return price

        logger.warning("No parseable price found on Target page for %s", product_id)
        return None

    def get_product_info(self, product_id: str) -> Dict:
        """Get detailed product information"""
        url = f"{self.BASE_URL}/p/{product_id}"
        soup = self._get_soup(url)

        # Extract product name
        name_element = soup.select_one('[data-test="product-title"]')
        name = name_element.get_text().strip() if name_element else "Unknown"

        # Extract price
        price = self.get_product_price(product_id)

        # Extract category from breadcrumb
        category_element = soup.select_one('[data-test="breadcrumb"]')
        category = "Unknown"
        if category_element:
            breadcrumbs = category_element.select('a')
            if breadcrumbs:
                category = breadcrumbs[-1].get_text().strip()

        return {
            'name': name,
            'url': url,
            'category': category,
            'price': price,
            'description': ''
        }

    def search_products(self, query: str, category: str = None) -> List[Dict]:
        """Search for products on Target"""
        url = f"{self.BASE_URL}/s"
        params = {
            'searchTerm': query,
            'category': category,
            'sortName': 'bestselling'
        }

        soup = self._get_soup(url, params=params)
        products = []

        # Target product cards
        product_cards = soup.select('[data-test="product-card"]')
        skipped = 0

        for card in product_cards[:20]:  # Limit to 20 results
            # Extract TCIN from data attribute
            tcin = card.get('data-tcin')
            if not tcin:
                skipped += 1
                continue

            # Extract name
            name_element = card.select_one('[data-test="product-title"]')
            name = name_element.get_text().strip() if name_element else "Unknown"

            # Extract price
            price_element = card.select_one('[data-test="product-price"]')
            price = self._parse_price(price_element.get_text()) if price_element else None

            # Extract URL
            link_element = card.select_one('a[href*="/p/"]')
            product_url = (
                f"{self.BASE_URL}{link_element['href']}" if link_element
                else f"{self.BASE_URL}/p/{tcin}"
            )

            products.append({
                'product_id': tcin,
                'name': name,
                'url': product_url,
                'category': category or 'Unknown',
                'price': price,
                'retailer': 'target'
            })

        if skipped:
            logger.warning("Skipped %s Target result cards without a TCIN", skipped)
        if product_cards and not products:
            raise ScraperError(
                f"Target returned {len(product_cards)} cards for {query!r} but none could be parsed"
            )

        return products

    def get_trending_products(self, category: str = 'all') -> List[Dict]:
        """Get trending products from Target"""
        # Target doesn't have a public trending API, so we'll search popular terms
        popular_searches = [
            'electronics', 'home goods', 'kitchen', 'furniture', 
            'toys', 'beauty', 'clothing', 'appliances'
        ]
        
        search_term = category if category != 'all' else popular_searches[0]
        return self.search_products(search_term, category)
