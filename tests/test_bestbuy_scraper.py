import pytest
import requests

from scrapers.bestbuy import BestBuyScraper


@pytest.fixture
def scraper(config):
    return BestBuyScraper(config)


def patch_get(monkeypatch, response, recorder=None):
    def fake_get(url, params=None, headers=None, **kwargs):
        if recorder is not None:
            recorder.append({'url': url, 'params': params, 'headers': headers})
        if isinstance(response, Exception):
            raise response
        return response

    monkeypatch.setattr(requests, 'get', fake_get)


def test_get_product_price_prefers_sale_price(scraper, monkeypatch, fake_response):
    calls = []
    patch_get(monkeypatch, fake_response([{'salePrice': 79.99, 'regularPrice': 99.99}]), calls)

    assert scraper.get_product_price('6412345') == 79.99
    assert calls[0]['url'].endswith('/6412345.json')
    assert calls[0]['params']['apiKey'] == 'bb-key'


def test_get_product_price_falls_back_to_regular_price(scraper, monkeypatch, fake_response):
    patch_get(monkeypatch, fake_response([{'salePrice': None, 'regularPrice': 99.99}]))

    assert scraper.get_product_price('6412345') == 99.99


def test_get_product_price_returns_none_for_empty_payload(scraper, monkeypatch, fake_response):
    patch_get(monkeypatch, fake_response([]))

    assert scraper.get_product_price('6412345') is None


def test_get_product_price_returns_none_on_request_error(scraper, monkeypatch):
    patch_get(monkeypatch, requests.RequestException('boom'))

    assert scraper.get_product_price('6412345') is None


def test_get_product_info_maps_fields(scraper, monkeypatch, fake_response):
    patch_get(monkeypatch, fake_response([{
        'name': 'Widget',
        'url': 'https://bestbuy.com/widget',
        'categoryPath': ['Electronics', 'Audio'],
        'salePrice': 10.0,
        'regularPrice': 20.0,
        'description': 'A widget',
        'image': 'https://img/widget.jpg',
    }]))

    info = scraper.get_product_info('1')

    assert info == {
        'name': 'Widget',
        'url': 'https://bestbuy.com/widget',
        'category': 'Electronics',
        'price': 10.0,
        'regular_price': 20.0,
        'description': 'A widget',
        'image': 'https://img/widget.jpg',
    }


def test_get_product_info_defaults_category_when_missing(scraper, monkeypatch, fake_response):
    patch_get(monkeypatch, fake_response([{'name': 'Widget', 'categoryPath': []}]))

    assert scraper.get_product_info('1')['category'] == 'Unknown'


def test_get_product_info_returns_empty_dict_on_error(scraper, monkeypatch):
    patch_get(monkeypatch, requests.RequestException('boom'))

    assert scraper.get_product_info('1') == {}


def test_search_products_normalizes_results(scraper, monkeypatch, fake_response):
    calls = []
    patch_get(monkeypatch, fake_response([
        {'sku': 111, 'name': 'A', 'url': 'https://a', 'categoryPath': ['Tools'], 'salePrice': 5.0},
        {'sku': 222, 'name': 'B', 'url': 'https://b', 'categoryPath': None, 'regularPrice': 6.0},
    ]), calls)

    products = scraper.search_products('drill', category='abcat0900000')

    assert [p['product_id'] for p in products] == ['111', '222']
    assert products[0]['category'] == 'Tools'
    assert products[1]['category'] == 'Unknown'
    assert products[1]['price'] == 6.0
    assert {p['retailer'] for p in products} == {'bestbuy'}
    assert calls[0]['params']['categoryPath.id'] == 'abcat0900000'


def test_search_products_omits_category_filter_when_not_given(scraper, monkeypatch, fake_response):
    calls = []
    patch_get(monkeypatch, fake_response([]), calls)

    scraper.search_products('drill')

    assert 'categoryPath.id' not in calls[0]['params']


def test_search_products_returns_empty_list_on_error(scraper, monkeypatch):
    patch_get(monkeypatch, requests.RequestException('boom'))

    assert scraper.search_products('drill') == []


def test_get_trending_products_requests_best_sellers(scraper, monkeypatch, fake_response):
    calls = []
    patch_get(monkeypatch, fake_response([
        {'sku': 333, 'name': 'C', 'url': 'https://c', 'categoryPath': ['Home'], 'salePrice': 7.0},
    ]), calls)

    products = scraper.get_trending_products()

    assert products[0]['product_id'] == '333'
    assert calls[0]['params']['sort'] == 'bestSelling.desc'
    assert 'categoryPath.id' not in calls[0]['params']


def test_get_trending_products_scopes_to_category(scraper, monkeypatch, fake_response):
    calls = []
    patch_get(monkeypatch, fake_response([]), calls)

    scraper.get_trending_products('abcat0100000')

    assert calls[0]['params']['categoryPath.id'] == 'abcat0100000'


def test_get_trending_products_returns_empty_list_on_error(scraper, monkeypatch):
    patch_get(monkeypatch, requests.RequestException('boom'))

    assert scraper.get_trending_products() == []
