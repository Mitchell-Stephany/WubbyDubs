from abc import ABC, abstractmethod
from typing import Dict, Optional
import random
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from fake_useragent import UserAgent

class AdvancedScraper(ABC):
    """Advanced scraper with anti-detection techniques"""
    
    def __init__(self, config):
        self.config = config
        self.ua = UserAgent()
        self.driver = None
        self._init_driver()
    
    def _init_driver(self):
        """Initialize Chrome driver with anti-detection"""
        options = Options()
        
        # Anti-detection options
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-gpu')
        options.add_argument('--disable-software-rasterizer')
        options.add_argument('--disable-extensions')
        options.add_argument('--disable-infobars')
        options.add_argument('--start-maximized')
        options.add_argument('--disable-notifications')
        options.add_argument('--disable-popup-blocking')
        
        # User agent rotation
        options.add_argument(f'user-agent={self.ua.random}')
        
        # Set window size to look more like a real user
        options.add_argument('--window-size=1920,1080')
        
        try:
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=options)
            
            # Execute script to hide webdriver property
            self.driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
                "source": """
                    Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                    })
                """
            })
            
            # Set timeouts
            self.driver.set_page_load_timeout(30)
            self.driver.implicitly_wait(10)
            
            print("Advanced scraper initialized with anti-detection")
        except Exception as e:
            print(f"Failed to initialize advanced scraper: {e}")
            self.driver = None
    
    def _random_delay(self, min_seconds=2, max_seconds=5):
        """Add random delay to avoid detection"""
        delay = random.uniform(min_seconds, max_seconds)
        time.sleep(delay)
    
    def _random_headers(self) -> Dict[str, str]:
        """Generate random headers"""
        return {
            'User-Agent': self.ua.random,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Cache-Control': 'max-age=0',
        }
    
    def _safe_get_element_text(self, by, value, timeout=10):
        """Safely get element text with timeout"""
        try:
            element = WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located((by, value))
            )
            return element.text.strip()
        except:
            return None
    
    def _safe_get_element_attribute(self, by, value, attribute, timeout=10):
        """Safely get element attribute with timeout"""
        try:
            element = WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located((by, value))
            )
            return element.get_attribute(attribute)
        except:
            return None
    
    def close(self):
        """Close the driver"""
        if self.driver:
            self.driver.quit()
    
    def __del__(self):
        """Cleanup on deletion"""
        self.close()
    
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