from abc import ABC, abstractmethod
from typing import Dict, Optional
import requests
from fake_useragent import UserAgent

class BaseScraper(ABC):
    """Base class for all retailer scrapers"""
    
    def __init__(self, config):
        self.config = config
        self.ua = UserAgent()
        self.session = requests.Session()
    
    def _get_headers(self) -> Dict[str, str]:
        """Get headers with random user agent"""
        return {
            'User-Agent': self.ua.random,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
        }

    def _get(self, url: str, params: Dict = None) -> requests.Response:
        """Perform a GET request with a timeout, raising requests.RequestException on failure."""
        timeout = getattr(self.config, 'REQUEST_TIMEOUT_SECONDS', 15.0)
        response = self.session.get(
            url, params=params, headers=self._get_headers(), timeout=timeout
        )
        response.raise_for_status()
        return response
    
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
