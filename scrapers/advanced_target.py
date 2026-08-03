import logging
from typing import Dict, Optional, List
from selenium.common.exceptions import NoSuchElementException, WebDriverException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from .advanced_base import AdvancedScraper

logger = logging.getLogger(__name__)

class AdvancedTargetScraper(AdvancedScraper):
    """Advanced Target scraper with anti-detection"""
    
    BASE_URL = "https://www.target.com"
    
    def get_product_price(self, product_id: str) -> Optional[float]:
        """Get current price for a product using TCIN"""
        url = f"{self.BASE_URL}/p/{product_id}"
        self.driver.get(url)
        self._random_delay(3, 6)

        # Try multiple price selectors
        price_selectors = [
            (By.CSS_SELECTOR, '[data-test="product-price"]'),
            (By.CSS_SELECTOR, '.Price-characteristic'),
            (By.CSS_SELECTOR, '.style__PriceText___2HiQw'),
            (By.CSS_SELECTOR, 'span[data-test="product-price"]'),
            (By.XPATH, '//span[contains(@class, "Price")]'),
        ]

        for by, selector in price_selectors:
            price_text = self._safe_get_element_text(by, selector, timeout=5)
            if not price_text:
                continue
            try:
                return float(price_text.replace('$', '').replace(',', '').strip())
            except ValueError:
                logger.debug("Unparseable Target price text %r from %s", price_text, selector)

        logger.warning("No parseable price found on Target page for %s", product_id)
        return None
    
    def get_product_info(self, product_id: str) -> Dict:
        """Get detailed product information"""
        url = f"{self.BASE_URL}/p/{product_id}"
        self.driver.get(url)
        self._random_delay(3, 6)

        # Extract product name
        name = self._safe_get_element_text(By.CSS_SELECTOR, '[data-test="product-title"]', timeout=10)
        if not name:
            name = self._safe_get_element_text(By.TAG_NAME, 'h1', timeout=10)

        # Extract price
        price = self.get_product_price(product_id)

        # Extract category from breadcrumb
        category = "Unknown"
        try:
            breadcrumbs = self.driver.find_elements(By.CSS_SELECTOR, '[data-test="breadcrumb"] a')
            if breadcrumbs:
                category = breadcrumbs[-1].text.strip()
        except NoSuchElementException:
            logger.debug("No breadcrumb on Target page for %s", product_id)

        return {
            'name': name or "Unknown",
            'url': url,
            'category': category,
            'price': price,
            'description': ''
        }
    
    def _card_price(self, card) -> Optional[float]:
        """Price shown on a search result card, or None when it is absent."""
        try:
            price_text = card.find_element(By.CSS_SELECTOR, '[data-test="product-price"]').text.strip()
        except NoSuchElementException:
            return None
        try:
            return float(price_text.replace('$', '').replace(',', ''))
        except ValueError:
            logger.debug("Unparseable Target card price %r", price_text)
            return None

    def search_products(self, query: str, category: str = None, limit: int = 20) -> List[Dict]:
        """Search for products on Target"""
        url = f"{self.BASE_URL}/s"
        self.driver.get(url)
        self._random_delay(2, 4)

        # Find search input and enter query
        search_input = WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, 'input[type="search"], input[name="searchTerm"]'))
        )
        search_input.clear()
        search_input.send_keys(query)
        self._random_delay(1, 2)

        # Submit search
        search_input.submit()
        self._random_delay(3, 5)

        products = []
        product_cards = self.driver.find_elements(By.CSS_SELECTOR, '[data-test="product-card"]')
        skipped = 0

        for card in product_cards[:limit]:
            # Extract TCIN from data attribute
            tcin = card.get_attribute('data-tcin')
            if not tcin:
                skipped += 1
                continue

            try:
                # Extract name
                name_element = card.find_element(By.CSS_SELECTOR, '[data-test="product-title"]')
                name = name_element.text.strip() if name_element else "Unknown"

                price = self._card_price(card)

                # Extract URL
                link_element = card.find_element(By.CSS_SELECTOR, 'a[href*="/p/"]')
                product_url = f"{self.BASE_URL}{link_element.get_attribute('href')}" if link_element else f"{self.BASE_URL}/p/{tcin}"
            except (NoSuchElementException, WebDriverException):
                logger.warning("Could not parse a Target product card", exc_info=True)
                skipped += 1
                continue

            products.append({
                'product_id': tcin,
                'name': name,
                'url': product_url,
                'category': category or 'Unknown',
                'price': price,
                'retailer': 'target'
            })

            self._random_delay(0.5, 1.5)  # Small delay between products

        if skipped:
            logger.warning("Skipped %s unparseable Target product cards", skipped)

        return products
    
    def get_trending_products(self, category: str = 'all', limit: int = 20) -> List[Dict]:
        """Get trending products from Target"""
        popular_searches = [
            'electronics', 'home goods', 'kitchen', 'furniture', 
            'toys', 'beauty', 'clothing', 'appliances'
        ]
        
        search_term = category if category != 'all' else popular_searches[0]
        return self.search_products(search_term, category, limit)