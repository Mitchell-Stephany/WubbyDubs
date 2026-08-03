import logging
from typing import Dict, Optional, List
from selenium.common.exceptions import NoSuchElementException, WebDriverException
from selenium.webdriver.common.by import By
from .advanced_base import AdvancedScraper

logger = logging.getLogger(__name__)

class AdvancedHomeDepotScraper(AdvancedScraper):
    """Advanced Home Depot scraper with anti-detection"""
    
    BASE_URL = "https://www.homedepot.com"
    
    def get_product_price(self, product_id: str) -> Optional[float]:
        """Get current price for a product using product ID"""
        url = f"{self.BASE_URL}/p/{product_id}"
        self.driver.get(url)
        self._random_delay(3, 6)

        # Try multiple price selectors
        price_selectors = [
            (By.CSS_SELECTOR, '[data-testid="product-price"]'),
            (By.CSS_SELECTOR, '.price__format'),
            (By.CSS_SELECTOR, '.price-dollars'),
            (By.CSS_SELECTOR, '.price-cents'),
            (By.CSS_SELECTOR, '.product-price'),
            (By.XPATH, '//div[contains(@class, "price")]'),
        ]

        for by, selector in price_selectors:
            price_text = self._safe_get_element_text(by, selector, timeout=5)
            if not price_text:
                continue
            try:
                return float(price_text.replace('$', '').replace(',', '').strip())
            except ValueError:
                logger.debug("Unparseable Home Depot price text %r from %s", price_text, selector)

        logger.warning("No parseable price found on Home Depot page for %s", product_id)
        return None
    
    def get_product_info(self, product_id: str) -> Dict:
        """Get detailed product information"""
        url = f"{self.BASE_URL}/p/{product_id}"
        self.driver.get(url)
        self._random_delay(3, 6)

        # Extract product name
        name = self._safe_get_element_text(By.CSS_SELECTOR, 'h1.product-title', timeout=10)
        if not name:
            name = self._safe_get_element_text(By.TAG_NAME, 'h1', timeout=10)

        # Extract price
        price = self.get_product_price(product_id)

        # Extract category from breadcrumb
        category = "Unknown"
        try:
            category_elements = self.driver.find_elements(By.CSS_SELECTOR, '.breadcrumb a')
            if category_elements:
                category = category_elements[-1].text.strip()
        except NoSuchElementException:
            logger.debug("No breadcrumb on Home Depot page for %s", product_id)

        return {
            'name': name or "Unknown",
            'url': url,
            'category': category,
            'price': price,
            'description': ''
        }
    
    def search_products(self, query: str, category: str = None, limit: int = 20) -> List[Dict]:
        """Search for products on Home Depot"""
        url = f"{self.BASE_URL}/s/{query}"
        self.driver.get(url)
        self._random_delay(3, 5)

        products = []
        product_cards = self.driver.find_elements(By.CSS_SELECTOR, '.product-pod')
        skipped = 0

        for card in product_cards[:limit]:
            try:
                # Extract product ID from URL
                link_element = card.find_element(By.CSS_SELECTOR, 'a.product-pod__link')
                product_url = link_element.get_attribute('href')
                if not product_url or '/p/' not in product_url:
                    skipped += 1
                    continue

                product_id = product_url.split('/p/')[-1].split('/')[0]

                # Extract name
                name_element = card.find_element(By.CSS_SELECTOR, '.product-pod__title')
                name = name_element.text.strip() if name_element else "Unknown"
            except (NoSuchElementException, WebDriverException):
                logger.warning("Could not parse a Home Depot product card", exc_info=True)
                skipped += 1
                continue

            products.append({
                'product_id': product_id,
                'name': name,
                'url': f"{self.BASE_URL}{product_url}",
                'category': category or 'Unknown',
                'price': self._card_price(card),
                'retailer': 'homedepot'
            })

            self._random_delay(0.5, 1.5)  # Small delay between products

        if skipped:
            logger.warning("Skipped %s unparseable Home Depot product cards", skipped)

        return products

    def _card_price(self, card) -> Optional[float]:
        """Price shown on a search result card, or None when it is absent."""
        try:
            price_text = card.find_element(By.CSS_SELECTOR, '.price__format').text.strip()
        except NoSuchElementException:
            return None
        try:
            return float(price_text.replace('$', '').replace(',', ''))
        except ValueError:
            logger.debug("Unparseable Home Depot card price %r", price_text)
            return None
    
    def get_trending_products(self, category: str = 'all', limit: int = 20) -> List[Dict]:
        """Get trending products from Home Depot"""
        popular_searches = [
            'tools', 'appliances', 'kitchen', 'bathroom', 
            'lighting', 'flooring', 'paint', 'lawn'
        ]
        
        search_term = category if category != 'all' else popular_searches[0]
        return self.search_products(search_term, category, limit)