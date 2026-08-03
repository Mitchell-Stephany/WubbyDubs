"""Shared helpers used across scrapers, analysis and notification modules."""

from typing import Dict, List, Optional

BASE_HEADERS = {
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.5',
    'Accept-Encoding': 'gzip, deflate',
    'Connection': 'keep-alive',
}


def build_headers(user_agent: str, extra: Dict[str, str] = None) -> Dict[str, str]:
    """Build request headers for a given user agent"""
    headers = dict(BASE_HEADERS)
    headers['User-Agent'] = user_agent
    if extra:
        headers.update(extra)
    return headers


def parse_price(price_text: Optional[str]) -> Optional[float]:
    """Parse a displayed price such as "$1,234.56" into a float"""
    if not price_text:
        return None

    cleaned = price_text.replace('$', '').replace(',', '').strip()
    try:
        return float(cleaned)
    except ValueError:
        return None


def calculate_drop_percentage(previous_price: float, current_price: float) -> float:
    """Percentage the price dropped relative to the previous price"""
    if not previous_price or previous_price <= 0:
        return 0.0
    return ((previous_price - current_price) / previous_price) * 100


def build_product_record(product_id: str, name: str, url: str, retailer: str,
                         price: Optional[float] = None, category: str = None,
                         **extra) -> Dict:
    """Build the product dictionary shape shared by every scraper"""
    product = {
        'product_id': product_id,
        'name': name,
        'url': url,
        'category': category or 'Unknown',
        'price': price,
        'retailer': retailer,
    }
    product.update(extra)
    return product


def pick_search_term(category: Optional[str], popular_searches: List[str]) -> str:
    """Pick a search term for trending lookups on retailers without a trending API"""
    if category and category != 'all':
        return category
    return popular_searches[0]
