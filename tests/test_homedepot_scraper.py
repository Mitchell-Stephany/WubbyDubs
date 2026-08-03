import pytest
import requests

from scrapers.homedepot import HomeDepotScraper


@pytest.fixture
def scraper(config):
    return HomeDepotScraper(config)


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
  <h1 class="product-title">Cordless Drill</h1>
  <div data-testid="product-price">$1,049.00</div>
  <div class="breadcrumb"><a>Tools</a><a>Power Tools</a></div>
</body></html>
"""


def test_get_product_price_parses_price(scraper, monkeypatch, fake_response):
    calls = []
    patch_get(monkeypatch, fake_response(text=PRODUCT_PAGE), calls)

    assert scraper.get_product_price('305626551') == 1049.00
    assert calls[0]['url'] == 'https://www.homedepot.com/p/305626551'


def test_get_product_price_skips_unparseable_selector(scraper, monkeypatch, fake_response):
    html = '<div data-testid="product-price">See price in cart</div><div class="price__format">89.99</div>'
    patch_get(monkeypatch, fake_response(text=html))

    assert scraper.get_product_price('1') == 89.99


def test_get_product_price_returns_none_when_absent(scraper, monkeypatch, fake_response):
    patch_get(monkeypatch, fake_response(text='<html></html>'))

    assert scraper.get_product_price('1') is None


def test_get_product_price_returns_none_on_request_error(scraper, monkeypatch):
    patch_get(monkeypatch, requests.RequestException('blocked'))

    assert scraper.get_product_price('1') is None


def test_get_product_info_extracts_fields(scraper, monkeypatch, fake_response):
    patch_get(monkeypatch, fake_response(text=PRODUCT_PAGE))

    info = scraper.get_product_info('305626551')

    assert info['name'] == 'Cordless Drill'
    assert info['category'] == 'Power Tools'
    assert info['price'] == 1049.00


def test_get_product_info_uses_unknown_defaults(scraper, monkeypatch, fake_response):
    patch_get(monkeypatch, fake_response(text='<html></html>'))

    info = scraper.get_product_info('1')

    assert info['name'] == 'Unknown'
    assert info['category'] == 'Unknown'


def test_get_product_info_returns_empty_dict_on_error(scraper, monkeypatch):
    patch_get(monkeypatch, requests.RequestException('blocked'))

    assert scraper.get_product_info('1') == {}


SEARCH_PAGE = """
<html><body>
  <div class="product-pod">
    <a class="product-pod__link" href="/p/305626551">Drill</a>
    <span class="product-pod__title">Cordless Drill</span>
    <span class="price__format">$99.00</span>
  </div>
  <div class="product-pod">
    <a class="product-pod__link" href="/b/category">Category</a>
  </div>
  <div class="product-pod"><span class="product-pod__title">No link</span></div>
</body></html>
"""


def test_search_products_parses_cards_and_skips_invalid_ones(scraper, monkeypatch, fake_response):
    patch_get(monkeypatch, fake_response(text=SEARCH_PAGE))

    products = scraper.search_products('drill', category='tools')

    assert len(products) == 1
    assert products[0] == {
        'product_id': '305626551',
        'name': 'Cordless Drill',
        'url': 'https://www.homedepot.com/p/305626551',
        'category': 'tools',
        'price': 99.00,
        'retailer': 'homedepot',
    }


def test_search_products_takes_first_path_segment_after_p_as_id(scraper, monkeypatch, fake_response):
    html = '''
    <div class="product-pod">
      <a class="product-pod__link" href="/p/Brand-Cordless-Drill/305626551">Drill</a>
      <span class="product-pod__title">Cordless Drill</span>
    </div>
    '''
    patch_get(monkeypatch, fake_response(text=html))

    products = scraper.search_products('drill')

    assert products[0]['product_id'] == 'Brand-Cordless-Drill'


def test_search_products_passes_category_filter(scraper, monkeypatch, fake_response):
    calls = []
    patch_get(monkeypatch, fake_response(text='<html></html>'), calls)

    scraper.search_products('drill', category='tools')

    assert calls[0]['url'] == 'https://www.homedepot.com/s/drill'
    assert calls[0]['params']['M'] == 'tools'


def test_search_products_returns_empty_list_on_error(scraper, monkeypatch):
    patch_get(monkeypatch, requests.RequestException('blocked'))

    assert scraper.search_products('drill') == []


def test_get_trending_products_uses_default_term_for_all(scraper, monkeypatch):
    calls = []
    monkeypatch.setattr(
        scraper, 'search_products',
        lambda query, category=None: calls.append((query, category)) or [],
    )

    scraper.get_trending_products()
    scraper.get_trending_products('paint')

    assert calls == [('tools', 'all'), ('paint', 'paint')]
