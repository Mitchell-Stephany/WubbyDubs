"""
Browser-based scraper using Playwright with stealth mode.
Bypasses anti-bot measures by simulating a real browser.
"""

import asyncio
import json
import re
import hashlib
import random
from typing import Dict, Optional, List
from playwright.async_api import async_playwright, Browser, BrowserContext, Page
from bs4 import BeautifulSoup

class BrowserScraper:
    """Playwright-based scraper with stealth mode for anti-bot bypass
    
    Uses Chromium for Amazon/Walmart and Firefox for Target (better anti-bot bypass).
    Home Depot and Lowe's are blocked even with browser automation.
    """
    
    def __init__(self, config=None, headless: bool = True):
        self.config = config
        self.headless = headless
        self._playwright = None
        self._chromium_browser: Optional[Browser] = None
        self._firefox_browser: Optional[Browser] = None
        self._chromium_context: Optional[BrowserContext] = None
        self._firefox_context: Optional[BrowserContext] = None
    
    async def _start_chromium(self):
        """Start Chromium browser with stealth settings"""
        if self._chromium_browser:
            return
        
        if not self._playwright:
            self._playwright = await async_playwright().start()
        
        self._chromium_browser = await self._playwright.chromium.launch(
            headless=self.headless,
            args=[
                '--disable-blink-features=AutomationControlled',
                '--disable-features=IsolateOrigins,site-per-process',
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-dev-shm-usage',
                '--disable-accelerated-2d-canvas',
                '--no-first-run',
                '--no-zygote',
                '--disable-gpu',
                '--hide-scrollbars',
                '--mute-audio',
                '--disable-background-timer-throttling',
                '--disable-backgrounding-occluded-windows',
                '--disable-renderer-backgrounding',
            ]
        )
        
        self._chromium_context = await self._chromium_browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
            locale='en-US',
            timezone_id='America/New_York',
            java_script_enabled=True,
            ignore_https_errors=True,
        )
        
        await self._chromium_context.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
            Object.defineProperty(navigator, 'plugins', { get: () => [1, 2, 3, 4, 5] });
            Object.defineProperty(navigator, 'languages', { get: () => ['en-US', 'en'] });
            window.chrome = { runtime: {} };
            const originalQuery = window.navigator.permissions.query;
            window.navigator.permissions.query = (parameters) =>
                parameters.name === 'notifications'
                    ? Promise.resolve({ state: Notification.permission })
                    : originalQuery(parameters);
        """)
    
    async def _start_firefox(self):
        """Start Firefox browser with stealth settings"""
        if self._firefox_browser:
            return
        
        if not self._playwright:
            self._playwright = await async_playwright().start()
        
        self._firefox_browser = await self._playwright.firefox.launch(
            headless=self.headless
        )
        
        self._firefox_context = await self._firefox_browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:131.0) Gecko/20100101 Firefox/131.0',
            locale='en-US',
            timezone_id='America/New_York',
            java_script_enabled=True,
            ignore_https_errors=True,
        )
        
        await self._firefox_context.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
            Object.defineProperty(navigator, 'plugins', { get: () => [1, 2, 3, 4, 5] });
            Object.defineProperty(navigator, 'languages', { get: () => ['en-US', 'en'] });
        """)
    
    async def _start(self):
        """Start both browsers"""
        await self._start_chromium()
        await self._start_firefox()
    
    async def _get_page(self, browser_type: str = 'chromium') -> Page:
        """Get a new page from specified browser"""
        if browser_type == 'firefox':
            if not self._firefox_browser:
                await self._start_firefox()
            page = await self._firefox_context.new_page()
        else:
            if not self._chromium_browser:
                await self._start_chromium()
            page = await self._chromium_context.new_page()
        
        await page.set_extra_http_headers({
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        })
        
        return page
    
    async def _random_delay(self, min_s: float = 2, max_s: float = 5):
        """Random human-like delay"""
        await asyncio.sleep(random.uniform(min_s, max_s))
    
    def _parse_price(self, price_text: str) -> Optional[float]:
        if not price_text:
            return None
        match = re.search(r'[\$£€]?\s*(\d+(?:[.,]\d+)?)', price_text)
        if match:
            try:
                return float(match.group(1).replace(',', ''))
            except ValueError:
                return None
        return None
    
    async def _navigate_with_retry(self, page: Page, url: str, wait_selector: str = None, retries: int = 3) -> bool:
        """Navigate to URL with retry logic and human-like behavior"""
        for attempt in range(retries):
            try:
                response = await page.goto(url, wait_until='domcontentloaded', timeout=30000)
                
                if response and response.status == 200:
                    # Wait for content to load
                    await self._random_delay(2, 4)
                    
                    # Scroll down like a human
                    await page.evaluate('window.scrollTo(0, 500)')
                    await self._random_delay(1, 2)
                    await page.evaluate('window.scrollTo(0, 1000)')
                    await self._random_delay(1, 2)
                    
                    if wait_selector:
                        try:
                            await page.wait_for_selector(wait_selector, timeout=10000)
                        except:
                            pass
                    
                    return True
                elif response and response.status in [403, 429, 503]:
                    print(f"  Blocked (status {response.status}), retrying...")
                    await self._random_delay(5, 10)
                    continue
                else:
                    return False
                    
            except Exception as e:
                print(f"  Navigation error: {e}")
                await self._random_delay(3, 6)
                continue
        
        return False
    
    async def search_amazon(self, query: str, limit: int = 10) -> List[Dict]:
        """Search Amazon using browser automation"""
        products = []
        
        try:
            page = await self._get_page()
            url = f"https://www.amazon.com/s?k={query.replace(' ', '+')}&s=price-asc-rank"
            
            print(f"  [Browser] Searching Amazon for '{query}'...")
            success = await self._navigate_with_retry(page, url, '[data-component-type="s-search-result"]')
            
            if not success:
                print(f"  Amazon navigation failed")
                await page.close()
                return []
            
            # Wait for products to render
            await self._random_delay(2, 3)
            
            # Extract products using JavaScript
            products = await page.evaluate('''(limit) => {
                const products = [];
                const elements = document.querySelectorAll('[data-component-type="s-search-result"]');
                
                for (const element of elements) {
                    if (products.length >= limit) break;
                    
                    const asin = element.getAttribute('data-asin') || '';
                    
                    // Get name
                    let name = '';
                    const nameEl = element.querySelector('h2 a span') || element.querySelector('h2 span') || element.querySelector('h2 a');
                    if (nameEl) name = nameEl.textContent.trim();
                    
                    if (!name || name === 'Results' || name.length < 5) continue;
                    
                    // Get price - try multiple methods
                    let price = 0;
                    
                    // Method 1: a-offscreen
                    const priceEls = element.querySelectorAll('.a-offscreen');
                    for (const el of priceEls) {
                        const text = el.textContent.trim();
                        if (text.includes('$')) {
                            const match = text.match(/\\$([\\d,]+\\.?\\d*)/);
                            if (match) {
                                price = parseFloat(match[1].replace(',', ''));
                                if (price > 0) break;
                            }
                        }
                    }
                    
                    // Method 2: search text nodes
                    if (price === 0) {
                        const allText = element.textContent;
                        const matches = allText.match(/\\$([\\d,]+\\.?\\d*)/g);
                        if (matches) {
                            for (const m of matches) {
                                const val = parseFloat(m.replace('$', '').replace(',', ''));
                                if (val > 0 && !m.includes('delivery') && !m.includes('shipping')) {
                                    price = val;
                                    break;
                                }
                            }
                        }
                    }
                    
                    // Get URL
                    let productUrl = asin ? `https://www.amazon.com/dp/${asin}` : '';
                    if (!productUrl) {
                        const linkEl = element.querySelector('h2 a');
                        if (linkEl) productUrl = linkEl.href;
                    }
                    
                    // Get image
                    let image = '';
                    const imgEl = element.querySelector('img.s-image');
                    if (imgEl) image = imgEl.src;
                    
                    if (name && name !== 'Results') {
                        products.push({
                            product_id: `amazon_${asin}`,
                            name: name,
                            url: productUrl,
                            category: 'General',
                            price: price,
                            retailer: 'Amazon',
                            image: image
                        });
                    }
                }
                return products;
            }''', limit)
            
            await page.close()
            print(f"  Extracted {len(products)} valid products from Amazon")
            return products[:limit]
            
        except Exception as e:
            print(f"  Amazon search error: {e}")
            return []
    
    async def search_walmart(self, query: str, limit: int = 10) -> List[Dict]:
        """Search Walmart using browser automation"""
        products = []
        
        try:
            page = await self._get_page()
            url = f"https://www.walmart.com/search?q={query.replace(' ', '+')}"
            
            print(f"  [Browser] Searching Walmart for '{query}'...")
            success = await self._navigate_with_retry(page, url)
            
            if not success:
                print(f"  Walmart navigation failed")
                await page.close()
                return []
            
            await self._random_delay(3, 5)
            
            # Try to extract from __NEXT_DATA__
            products = await page.evaluate('''(limit) => {
                const products = [];
                
                // Try __NEXT_DATA__
                const scriptEl = document.getElementById('__NEXT_DATA__');
                if (scriptEl) {
                    try {
                        const data = JSON.parse(scriptEl.textContent);
                        const props = data.props?.pageProps || {};
                        
                        // Walmart path: initialData.searchResult.itemStacks[0].items
                        let items = [];
                        const searchResult = props.initialData?.searchResult || {};
                        if (searchResult.itemStacks && searchResult.itemStacks.length > 0) {
                            // Combine items from all stacks
                            for (const stack of searchResult.itemStacks) {
                                const stackItems = stack.items || stack.itemsV2 || [];
                                items = items.concat(stackItems);
                            }
                        }
                        
                        for (const item of items) {
                            if (products.length >= limit) break;
                            const name = item.name || item.title || '';
                            if (!name || name.length < 5) continue;
                            
                            const priceInfo = item.priceInfo || {};
                            let price = 0;
                            // priceInfo.linePrice is a string like "$29.88"
                            const priceStr = priceInfo.linePrice || priceInfo.linePriceDisplay || priceInfo.itemPrice || '';
                            if (priceStr) {
                                const m = priceStr.match(/\\$?([\\d,]+\\.?\\d*)/);
                                if (m) price = parseFloat(m[1].replace(',', ''));
                            }
                            // Fallback to numeric price
                            if (!price) {
                                price = priceInfo.currentPrice || priceInfo.price || 0;
                            }
                            
                            const itemId = item.usItemId || item.id || item.itemId || '';
                            let productUrl = item.canonicalUrl || item.url || '';
                            if (productUrl && !productUrl.startsWith('http')) {
                                productUrl = 'https://www.walmart.com' + productUrl;
                            }
                            
                            if (name && price > 0) {
                                products.push({
                                    product_id: `walmart_${itemId}`,
                                    name: name,
                                    url: productUrl,
                                    category: 'General',
                                    price: parseFloat(price),
                                    retailer: 'Walmart'
                                });
                            }
                        }
                    } catch(e) {}
                }
                
                // Fallback: CSS selectors
                if (products.length === 0) {
                    const elements = document.querySelectorAll('[data-item-id], [class*="product-card"]');
                    for (const el of elements) {
                        if (products.length >= limit) break;
                        const nameEl = el.querySelector('[data-automation-id="product-title"], span.lh-title, h3, [class*="title"]');
                        if (!nameEl) continue;
                        const name = nameEl.textContent.trim();
                        if (!name || name.length < 5) continue;
                        
                        let price = 0;
                        const priceEl = el.querySelector('[data-automation-id="product-price"], [class*="price"]');
                        if (priceEl) {
                            const m = priceEl.textContent.match(/\\$([\\d,]+\\.?\\d*)/);
                            if (m) price = parseFloat(m[1].replace(',', ''));
                        }
                        
                        const linkEl = el.querySelector('a[href*="/ip/"]');
                        let url = linkEl ? linkEl.href : '';
                        
                        if (name && price > 0) {
                            products.push({
                                product_id: `walmart_${name.substring(0, 10)}`,
                                name: name,
                                url: url,
                                category: 'General',
                                price: price,
                                retailer: 'Walmart'
                            });
                        }
                    }
                }
                
                return products;
            }''', limit)
            
            await page.close()
            print(f"  Extracted {len(products)} valid products from Walmart")
            return products[:limit]
            
        except Exception as e:
            print(f"  Walmart search error: {e}")
            return []
    
    async def search_target(self, query: str, limit: int = 10) -> List[Dict]:
        """Search Target using Firefox browser automation - Firefox bypasses Target's bot detection"""
        products = []
        
        try:
            page = await self._get_page(browser_type='firefox')
            url = f"https://www.target.com/s?searchTerm={query.replace(' ', '+')}"
            
            print(f"  [Browser/Firefox] Searching Target for '{query}'...")
            response = await page.goto(url, wait_until='domcontentloaded', timeout=30000)
            
            if not response or response.status != 200:
                print(f"  Target navigation failed")
                await page.close()
                return []
            
            # Wait for JS to render products
            await self._random_delay(10, 15)
            
            # Scroll to trigger lazy loading
            await page.evaluate('window.scrollTo(0, 800)')
            await self._random_delay(3, 5)
            
            # Extract products from rendered DOM - Target uses a[href*="/p/"] for product links
            products = await page.evaluate('''(limit) => {
                const products = [];
                const productLinks = Array.from(document.querySelectorAll('a[href*="/p/"]'));
                const seen = new Set();
                
                for (const link of productLinks) {
                    if (products.length >= limit) break;
                    
                    const href = link.href;
                    // Extract TCIN from URL
                    const tcinMatch = href.match(/\\/A-(\\d+)/);
                    const tcin = tcinMatch ? tcinMatch[1] : '';
                    
                    if (seen.has(tcin)) continue;
                    seen.add(tcin);
                    
                    // Get product name - try textContent, aria-label, img alt
                    let name = link.textContent.trim();
                    if (!name || name.length < 5) {
                        name = link.getAttribute('aria-label') || '';
                    }
                    if (!name || name.length < 5) {
                        const img = link.querySelector('img');
                        if (img) name = img.alt || '';
                    }
                    if (!name || name.length < 5) {
                        const parent = link.closest('[class*="ProductCard"], [class*="product"], article, div');
                        if (parent) {
                            const nameEl = parent.querySelector('h2, h3, [class*="title"], [class*="Title"], a[aria-label]');
                            if (nameEl) {
                                name = nameEl.textContent.trim() || nameEl.getAttribute('aria-label') || '';
                            }
                        }
                    }
                    
                    if (!name || name.length < 5) continue;
                    
                    // Get price - look in parent element
                    let price = 0;
                    const parent = link.closest('[class*="ProductCard"], [class*="product"], article, div') || link.parentElement;
                    if (parent) {
                        const priceEls = parent.querySelectorAll('[class*="price"], [class*="Price"], span');
                        for (const pel of priceEls) {
                            const text = pel.textContent.trim();
                            const m = text.match(/^\\$([\\d,]+\\.?\\d*)$/);
                            if (m) {
                                const val = parseFloat(m[1].replace(',', ''));
                                if (val > 0 && val < 100000) {
                                    price = val;
                                    break;
                                }
                            }
                        }
                    }
                    
                    if (name) {
                        products.push({
                            product_id: `target_${tcin || name.substring(0, 10)}`,
                            name: name,
                            url: href.split('#')[0].split('?')[0],
                            category: 'General',
                            price: price,
                            retailer: 'Target'
                        });
                    }
                }
                
                return products;
            }''', limit)
            
            await page.close()
            print(f"  Extracted {len(products)} valid products from Target")
            return products[:limit]
            
        except Exception as e:
            print(f"  Target search error: {e}")
            return []
    
    async def search_homedepot(self, query: str, limit: int = 10) -> List[Dict]:
        """Search Home Depot using browser automation - waits for JS rendering"""
        products = []
        
        try:
            page = await self._get_page()
            url = f"https://www.homedepot.com/s/{query.replace(' ', '+')}"
            
            print(f"  [Browser] Searching Home Depot for '{query}'...")
            
            # Home Depot blocks aggressively - try with longer waits
            response = await page.goto(url, wait_until='networkidle', timeout=45000)
            
            if not response or response.status != 200:
                print(f"  Home Depot navigation failed (status: {response.status if response else 'N/A'})")
                # Try waiting and retrying
                await self._random_delay(5, 10)
                response = await page.goto(url, wait_until='domcontentloaded', timeout=30000)
                if not response or response.status != 200:
                    await page.close()
                    return []
            
            # Wait for products to render
            await self._random_delay(5, 8)
            
            # Scroll to trigger lazy loading
            await page.evaluate('window.scrollTo(0, 500)')
            await self._random_delay(2, 3)
            
            # Try waiting for product selectors
            for selector in ['[data-automation-id="product-pod"]', '[class*="product-pod"]', '[data-component="ProductPod"]']:
                try:
                    await page.wait_for_selector(selector, timeout=10000)
                    break
                except:
                    continue
            
            await self._random_delay(2, 3)
            
            # Extract from rendered DOM
            products = await page.evaluate('''(limit) => {
                const products = [];
                
                // Try __NEXT_DATA__ first
                const scriptEl = document.getElementById('__NEXT_DATA__');
                if (scriptEl) {
                    try {
                        const data = JSON.parse(scriptEl.textContent);
                        const props = data.props?.pageProps || {};
                        let items = [];
                        
                        if (props.initialData?.searchModel?.items) {
                            items = props.initialData.searchModel.items;
                        } else if (props.searchModel?.items) {
                            items = props.searchModel.items;
                        } else if (props.items) {
                            items = props.items;
                        }
                        
                        for (const item of items) {
                            if (products.length >= limit) break;
                            const name = item.productLabel || item.description || '';
                            const price = item.pricing?.value || item.price || 0;
                            const itemId = item.itemId || item.id || '';
                            let productUrl = item.canonicalUrl || '';
                            if (productUrl && !productUrl.startsWith('http')) {
                                productUrl = 'https://www.homedepot.com' + productUrl;
                            }
                            
                            if (name && price > 0) {
                                products.push({
                                    product_id: `homedepot_${itemId}`,
                                    name: name,
                                    url: productUrl,
                                    category: 'General',
                                    price: parseFloat(price),
                                    retailer: 'Home Depot'
                                });
                            }
                        }
                    } catch(e) {}
                }
                
                // Fallback: CSS selectors on rendered DOM
                if (products.length === 0) {
                    const selectors = [
                        '[data-automation-id="product-pod"]',
                        '[class*="product-pod"]',
                        '[data-component="ProductPod"]',
                        'div[class*="ProductCard"]'
                    ];
                    let elements = [];
                    for (const sel of selectors) {
                        elements = document.querySelectorAll(sel);
                        if (elements.length > 0) break;
                    }
                    
                    for (const el of elements) {
                        if (products.length >= limit) break;
                        const nameEl = el.querySelector('[data-automation-id="product-pod__title"], h3, h2, [class*="title"]');
                        if (!nameEl) continue;
                        const name = nameEl.textContent.trim();
                        if (!name || name.length < 5) continue;
                        
                        let price = 0;
                        const priceEl = el.querySelector('[data-automation-id="product-pod__price"], [class*="price"]');
                        if (priceEl) {
                            const m = priceEl.textContent.match(/\\$([\\d,]+\\.?\\d*)/);
                            if (m) price = parseFloat(m[1].replace(',', ''));
                        }
                        
                        const linkEl = el.querySelector('a[href*="/p/"]');
                        let url = linkEl ? linkEl.href : '';
                        
                        products.push({
                            product_id: `homedepot_${name.substring(0, 10)}`,
                            name: name,
                            url: url,
                            category: 'General',
                            price: price,
                            retailer: 'Home Depot'
                        });
                    }
                }
                
                return products;
            }''', limit)
            
            await page.close()
            print(f"  Extracted {len(products)} valid products from Home Depot")
            return products[:limit]
            
        except Exception as e:
            print(f"  Home Depot search error: {e}")
            return []
    
    async def search_lowes(self, query: str, limit: int = 10) -> List[Dict]:
        """Search Lowe's using browser automation - waits for JS rendering"""
        products = []
        
        try:
            page = await self._get_page()
            url = f"https://www.lowes.com/search?searchTerm={query.replace(' ', '+')}"
            
            print(f"  [Browser] Searching Lowe's for '{query}'...")
            
            # Lowe's blocks aggressively - try with longer waits
            response = await page.goto(url, wait_until='networkidle', timeout=45000)
            
            if not response or response.status != 200:
                print(f"  Lowe's navigation failed (status: {response.status if response else 'N/A'})")
                await self._random_delay(5, 10)
                response = await page.goto(url, wait_until='domcontentloaded', timeout=30000)
                if not response or response.status != 200:
                    await page.close()
                    return []
            
            # Wait for products to render
            await self._random_delay(5, 8)
            
            # Scroll to trigger lazy loading
            await page.evaluate('window.scrollTo(0, 500)')
            await self._random_delay(2, 3)
            
            # Try waiting for product selectors
            for selector in ['[data-component="ProductCard"]', '[class*="product-card"]', '[class*="ProductCard"]', 'article']:
                try:
                    await page.wait_for_selector(selector, timeout=10000)
                    break
                except:
                    continue
            
            await self._random_delay(2, 3)
            
            # Extract from rendered DOM
            products = await page.evaluate('''(limit) => {
                const products = [];
                
                // Try __NEXT_DATA__ first
                const scriptEl = document.getElementById('__NEXT_DATA__');
                if (scriptEl) {
                    try {
                        const data = JSON.parse(scriptEl.textContent);
                        const props = data.props?.pageProps || {};
                        let items = [];
                        
                        if (props.search?.itemStacks) {
                            items = props.search.itemStacks[0]?.items || [];
                        } else if (props.initialData?.search?.items) {
                            items = props.initialData.search.items;
                        } else if (props.products) {
                            items = props.products;
                        }
                        
                        for (const item of items) {
                            if (products.length >= limit) break;
                            const name = item.productLabel || item.description || item.title || item.name || '';
                            const price = item.pricing?.value || item.price || 0;
                            const itemId = item.itemId || item.omniItemId || item.id || '';
                            let productUrl = item.canonicalUrl || item.url || '';
                            if (productUrl && !productUrl.startsWith('http')) {
                                productUrl = 'https://www.lowes.com' + productUrl;
                            }
                            
                            if (name && price > 0) {
                                products.push({
                                    product_id: `lowes_${itemId}`,
                                    name: name,
                                    url: productUrl,
                                    category: 'General',
                                    price: parseFloat(price),
                                    retailer: "Lowe's"
                                });
                            }
                        }
                    } catch(e) {}
                }
                
                // Fallback: CSS selectors on rendered DOM
                if (products.length === 0) {
                    const selectors = [
                        '[data-component="ProductCard"]',
                        '[class*="product-card"]',
                        '[class*="ProductCard"]',
                        'article[class*="product"]'
                    ];
                    let elements = [];
                    for (const sel of selectors) {
                        elements = document.querySelectorAll(sel);
                        if (elements.length > 0) break;
                    }
                    
                    for (const el of elements) {
                        if (products.length >= limit) break;
                        const nameEl = el.querySelector('[data-test="product-title"], h3, h2, [class*="title"], [class*="description"]');
                        if (!nameEl) continue;
                        const name = nameEl.textContent.trim();
                        if (!name || name.length < 5) continue;
                        
                        let price = 0;
                        const priceEls = el.querySelectorAll('[data-test="product-price"], [class*="price"], span');
                        for (const pel of priceEls) {
                            const text = pel.textContent.trim();
                            const m = text.match(/\\$([\\d,]+\\.?\\d*)/);
                            if (m) {
                                const val = parseFloat(m[1].replace(',', ''));
                                if (val > 0 && val < 100000) {
                                    price = val;
                                    break;
                                }
                            }
                        }
                        
                        const linkEl = el.querySelector('a[href*="/pd/"]');
                        let url = linkEl ? linkEl.href : '';
                        let url = linkEl ? linkEl.href : '';
                        
                        products.push({
                            product_id: `lowes_${name.substring(0, 10)}`,
                            name: name,
                            url: url,
                            category: 'General',
                            price: price,
                            retailer: "Lowe's"
                        });
                    }
                }
                
                return products;
            }''', limit)
            
            await page.close()
            print(f"  Extracted {len(products)} valid products from Lowe's")
            return products[:limit]
            
        except Exception as e:
            print(f"  Lowe's search error: {e}")
            return []
    
    async def get_product_price(self, url: str, retailer: str) -> Optional[float]:
        """Visit a product page directly and extract the current price.
        
        Much more efficient than searching - just 1 page load per product.
        
        Args:
            url: Direct product URL
            retailer: Retailer name (Amazon, Walmart, Target)
            
        Returns:
            Current price or None if not found
        """
        if not url:
            return None
        
        retailer_lower = retailer.lower()
        
        # Use Firefox for Target, Chromium for others
        browser_type = 'firefox' if 'target' in retailer_lower else 'chromium'
        
        try:
            page = await self._get_page(browser_type=browser_type)
            
            response = await page.goto(url, wait_until='domcontentloaded', timeout=30000)
            
            if not response or response.status != 200:
                await page.close()
                return None
            
            # Wait for page to render
            await self._random_delay(3, 5)
            
            # Extract price based on retailer
            price = await page.evaluate('''(retailer) => {
                const r = retailer.toLowerCase();
                let priceEls = [];
                
                if (r.includes('amazon')) {
                    // Amazon product page price selectors
                    priceEls = document.querySelectorAll(
                        '.a-price .a-offscreen, #priceblock_ourprice, #priceblock_dealprice, ' +
                        '#corePrice_feature_div .a-offscreen, .apexPriceToPay .a-offscreen, ' +
                        '[data-a-color="price"] .a-offscreen, #tp_price_block_total_price_ww .a-offscreen'
                    );
                } else if (r.includes('walmart')) {
                    // Walmart product page price - try multiple methods
                    priceEls = document.querySelectorAll(
                        '[itemprop="price"], .price-characteristic, [data-automation-id="product-price"], ' +
                        '[class*="price"] span, [class*="Price"] span'
                    );
                    // Try __NEXT_DATA__ (most reliable for Walmart)
                    if (priceEls.length === 0 || true) {
                        const script = document.getElementById('__NEXT_DATA__');
                        if (script) {
                            try {
                                const data = JSON.parse(script.textContent);
                                // Try multiple paths in Walmart's Next.js data
                                const product = data.props?.pageProps?.initialData?.data?.product || 
                                               data.props?.pageProps?.initialData?.data?.products?.[0] ||
                                               data.props?.pageProps?.product || {};
                                const priceInfo = product.priceInfo || product.price || {};
                                // Try various price fields
                                const priceStr = priceInfo.currentPrice?.price || 
                                                priceInfo.linePrice || 
                                                priceInfo.linePriceDisplay ||
                                                priceInfo.itemPrice ||
                                                (typeof priceInfo.currentPrice === 'number' ? priceInfo.currentPrice : '');
                                if (priceStr) {
                                    const m = String(priceStr).match(/\\$?([\\d,]+\\.?\\d*)/);
                                    if (m) {
                                        const val = parseFloat(m[1].replace(',', ''));
                                        if (val > 0 && val < 100000) return val;
                                    }
                                }
                            } catch(e) {}
                        }
                    }
                } else if (r.includes('target')) {
                    // Target product page price
                    priceEls = document.querySelectorAll(
                        '[data-test="product-price"], [class*="price"], [itemprop="price"]'
                    );
                }
                
                // Try each price element
                for (const el of priceEls) {
                    const text = el.textContent.trim();
                    const m = text.match(/\\$([\\d,]+\\.?\\d*)/);
                    if (m) {
                        const val = parseFloat(m[1].replace(',', ''));
                        if (val > 0 && val < 100000) return val;
                    }
                    // Also try content attribute for itemprop
                    const content = el.getAttribute('content') || el.getAttribute('data-automation-id');
                    if (content) {
                        const m2 = content.match(/([\\d,]+\\.?\\d*)/);
                        if (m2) {
                            const val = parseFloat(m2[1].replace(',', ''));
                            if (val > 0 && val < 100000) return val;
                        }
                    }
                }
                
                // Fallback: search for any $X.XX pattern
                const allText = document.body.innerText;
                const matches = allText.match(/\\$([\\d,]+\\.?\\d*)/g);
                if (matches) {
                    // Find the most likely product price (not shipping, not delivery)
                    for (const m of matches) {
                        const val = parseFloat(m.replace('$', '').replace(',', ''));
                        if (val > 0 && val < 100000) {
                            // Skip very low prices (likely shipping costs)
                            if (val < 1) continue;
                            return val;
                        }
                    }
                }
                
                return null;
            }''', retailer)
            
            await page.close()
            return price
            
        except Exception as e:
            print(f"    Price check error: {e}")
            return None
    
    async def search_all_retailers(self, query: str, limit_per_retailer: int = 3) -> List[Dict]:
        """Search all retailers"""
        all_products = []
        
        retailers = [
            ('amazon', self.search_amazon),
            ('walmart', self.search_walmart),
            ('target', self.search_target),
            ('homedepot', self.search_homedepot),
            ('lowes', self.search_lowes),
        ]
        
        for name, search_fn in retailers:
            try:
                products = await search_fn(query, limit_per_retailer)
                all_products.extend(products)
                await self._random_delay(3, 6)
            except Exception as e:
                print(f"  {name} failed: {e}")
        
        return all_products
    
    async def close(self):
        """Close browsers"""
        if self._chromium_context:
            await self._chromium_context.close()
        if self._chromium_browser:
            await self._chromium_browser.close()
        if self._firefox_context:
            await self._firefox_context.close()
        if self._firefox_browser:
            await self._firefox_browser.close()
        if self._playwright:
            await self._playwright.stop()
        self._chromium_context = None
        self._chromium_browser = None
        self._firefox_context = None
        self._firefox_browser = None
        self._playwright = None


def run_async_search(query: str, limit: int = 5, headless: bool = True) -> List[Dict]:
    """Synchronous wrapper for async browser scraping"""
    async def _run():
        scraper = BrowserScraper(headless=headless)
        try:
            await scraper._start()
            products = await scraper.search_all_retailers(query, limit)
            return products
        finally:
            await scraper.close()
    
    return asyncio.run(_run())
