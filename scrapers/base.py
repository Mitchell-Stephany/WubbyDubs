from abc import ABC, abstractmethod
from typing import Dict, List, Optional
import requests
from bs4 import BeautifulSoup
from fake_useragent import UserAgent

from utils import build_headers, parse_price

class BaseScraper(ABC):
    """Base class for all retailer scrapers"""
    
    DEFAULT_TIMEOUT = 15
    
    def __init__(self, config):
        self.config = config
        self.ua = UserAgent()
        self.session = requests.Session()
    
    def _get_headers(self) -> Dict[str, str]:
        """Get headers with random user agent"""
        return build_headers(self.ua.random)
    
    def _get(self, url: str, params: Dict = None, timeout: int = None) -> requests.Response:
        """Perform a GET request with scraper headers"""
        response = requests.get(
            url,
            params=params,
            headers=self._get_headers(),
            timeout=timeout or self.DEFAULT_TIMEOUT
        )
        response.raise_for_status()
        return response
    
    def _get_soup(self, url: str, params: Dict = None, timeout: int = None) -> BeautifulSoup:
        """Fetch a page and parse it into a BeautifulSoup document"""
        return BeautifulSoup(self._get(url, params, timeout).text, 'lxml')
    
    def _get_json(self, url: str, params: Dict = None, timeout: int = None):
        """Fetch a URL and decode the JSON body"""
        return self._get(url, params, timeout).json()
    
    @staticmethod
    def _select_price(soup, selectors: List[str]) -> Optional[float]:
        """Return the first price found using any of the given CSS selectors"""
        for selector in selectors:
            price = parse_price(BaseScraper._select_text(soup, selector))
            if price is not None:
                return price
        return None
    
    @staticmethod
    def _select_text(soup, selector: str, default: str = None) -> Optional[str]:
        """Return the stripped text of the first matching element"""
        element = soup.select_one(selector)
        return element.get_text().strip() if element else default
    
    @staticmethod
    def _select_breadcrumb_category(soup, selector: str) -> str:
        """Return the last breadcrumb entry, used as the product category"""
        breadcrumbs = soup.select(selector)
        return breadcrumbs[-1].get_text().strip() if breadcrumbs else "Unknown"
    
    @abstractmethod
    def get_product_price(self, product_id: str) -> Optional[float]:
        """Get current price for a product"""
        pass
    
    @abstractmethod
    def get_product_info(self, product_id: str) -> Dict:
        """Get product information"""
        pass
    
    @abstractmethod
    def search_products(self, query: str, category: str = None) -> list:
        """Search for products"""
        pass
