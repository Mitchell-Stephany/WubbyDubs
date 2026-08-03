import pytest
import requests

from scrapers.target import TargetScraper


@pytest.fixture
def scraper(config):
    return TargetScraper(config)


def patch_get(monkeypatch, response, recorder=None):
    def fake_get(url, params=None, headers=None, **kwargs):
        if recorder is not None:
            recorder.append({'url': url, 'params': params})
        if isinstance(response, Exception):
            raise response
        return response

    monkeypatch.setattr(requests, 'get', fake_get)


PRODUCT_PAGE = """
<html><body>
  <h1 data-test="product-title">Wireless Earbuds</h1>
  <span data-test="product-price">$1,299.99</span>
  <nav data-test="breadcrumb"><a href="/c/1">Electronics</a><a href="/c/2">Audio</a></nav>
</body></html>
"""


def test_get_product_price_parses_price_with_separators(scraper, monkeypatch, fake_response):
    calls = []
    patch_get(monkeypatch, fake_response(text=PRODUCT_PAGE), calls)

    assert scraper.get_product_price('54321') == 1299.99
    assert calls[0]['url'] == 'https://www.target.com/p/54321'


def test_get_product_price_falls_through_to_next_selector(scraper, monkeypatch, fake_response):
    html = '<span data-test="product-price">Sale</span><span class="Price-characteristic">42.50</span>'
    patch_get(monkeypatch, fake_response(text=html))

    assert scraper.get_product_price('1') == 42.50


def test_get_product_price_returns_none_when_no_price_found(scraper, monkeypatch, fake_response):
    patch_get(monkeypatch, fake_response(text='<html><body>nothing</body></html>'))

    assert scraper.get_product_price('1') is None


def test_get_product_price_returns_none_on_request_error(scraper, monkeypatch):
    patch_get(monkeypatch, requests.RequestException('blocked'))

    assert scraper.get_product_price('1') is None


def test_get_product_info_extracts_name_price_and_category(scraper, monkeypatch, fake_response):
    patch_get(monkeypatch, fake_response(text=PRODUCT_PAGE))

    info = scraper.get_product_info('54321')

    assert info['name'] == 'Wireless Earbuds'
    assert info['price'] == 1299.99
    assert info['category'] == 'Audio'
    assert info['url'] == 'https://www.target.com/p/54321'


def test_get_product_info_uses_unknown_defaults(scraper, monkeypatch, fake_response):
    patch_get(monkeypatch, fake_response(text='<html><body></body></html>'))

    info = scraper.get_product_info('54321')

    assert info['name'] == 'Unknown'
    assert info['category'] == 'Unknown'
    assert info['price'] is None


def test_get_product_info_returns_empty_dict_on_error(scraper, monkeypatch):
    patch_get(monkeypatch, requests.RequestException('blocked'))

    assert scraper.get_product_info('1') == {}


SEARCH_PAGE = """
<html><body>
  <div data-test="product-card" data-tcin="111">
    <span data-test="product-title">Product One</span>
    <span data-test="product-price">$19.99</span>
    <a href="/p/product-one/-/A-111">link</a>
  </div>
  <div data-test="product-card" data-tcin="222">
    <span data-test="product-price">from $5</span>
  </div>
  <div data-test="product-card"><span data-test="product-title">No TCIN</span></div>
</body></html>
"""


def test_search_products_parses_cards_and_skips_cards_without_tcin(scraper, monkeypatch, fake_response):
    calls = []
    patch_get(monkeypatch, fake_response(text=SEARCH_PAGE), calls)

    products = scraper.search_products('earbuds', category='electronics')

    assert [p['product_id'] for p in products] == ['111', '222']
    assert products[0]['name'] == 'Product One'
    assert products[0]['price'] == 19.99
    assert products[0]['url'] == 'https://www.target.com/p/product-one/-/A-111'
    assert products[0]['category'] == 'electronics'
    assert products[1]['name'] == 'Unknown'
    assert products[1]['price'] is None
    assert products[1]['url'] == 'https://www.target.com/p/222'
    assert calls[0]['params']['searchTerm'] == 'earbuds'


def test_search_products_returns_empty_list_on_error(scraper, monkeypatch):
    patch_get(monkeypatch, requests.RequestException('blocked'))

    assert scraper.search_products('earbuds') == []


def test_get_trending_products_searches_default_term_for_all(scraper, monkeypatch):
    calls = []
    monkeypatch.setattr(
        scraper, 'search_products',
        lambda query, category=None: calls.append((query, category)) or [],
    )

    scraper.get_trending_products()
    scraper.get_trending_products('tools')

    assert calls == [('electronics', 'all'), ('tools', 'tools')]
