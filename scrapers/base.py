from abc import ABC, abstractmethod
from typing import Dict, Optional
import re
import requests
from fake_useragent import UserAgent

PRODUCT_ID_PATTERN = re.compile(r'^[A-Za-z0-9._-]{1,64}$')
DOMAIN_PATTERN = re.compile(r'^(?!-)[A-Za-z0-9-]{1,63}(?<!-)(\.(?!-)[A-Za-z0-9-]{1,63}(?<!-))+$')


def validate_product_id(product_id: str) -> str:
    """Return the product id if it is safe to interpolate into a URL path"""
    if not isinstance(product_id, str) or not PRODUCT_ID_PATTERN.match(product_id):
        raise ValueError(f"Invalid product id: {product_id!r}")
    return product_id


def validate_domain(domain: str) -> str:
    """Return the domain if it is a plain hostname safe to build a URL from"""
    if not isinstance(domain, str) or not DOMAIN_PATTERN.match(domain):
        raise ValueError(f"Invalid domain: {domain!r}")
    return domain


class BaseScraper(ABC):
    """Base class for all retailer scrapers"""

    REQUEST_TIMEOUT = 15
    
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
