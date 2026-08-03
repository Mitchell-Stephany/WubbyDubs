import pytest
import requests

from scrapers.shoptera import ShopteraScraper


@pytest.fixture
def scraper(config):
    return ShopteraScraper(config)


def patch_get(monkeypatch, response, recorder=None):
    def fake_get(url, params=None, headers=None, timeout=None, **kwargs):
        if recorder is not None:
            recorder.append({'url': url, 'params': params, 'timeout': timeout})
        if isinstance(response, Exception):
            raise response
        return response

    monkeypatch.setattr(requests, 'get', fake_get)


def result(**overrides):
    item = {
        'title': 'Espresso Machine',
        'price': 100.0,
        'currency': 'EUR',
        'product_url': 'https://eshop.cz/products/espresso-machine',
        'image_url': 'https://img/1.jpg',
        'brand': 'DeLonghi',
        'category': 'kitchen',
        'eshop_name': 'Eshop',
        'eshop_domain': 'eshop.cz',
    }
    item.update(overrides)
    return item


def test_search_products_maps_and_converts_eur(scraper, monkeypatch, fake_response):
    calls = []
    patch_get(monkeypatch, fake_response({'results': [result()]}), calls)

    products = scraper.search_products('espresso', category='kitchen', min_price=10, max_price=200, limit=5)

    assert calls[0]['url'] == 'https://shoptera.ai/api/v1/search'
    assert calls[0]['params']['q'] == 'espresso'
    assert calls[0]['params']['limit'] == 5
    assert calls[0]['params']['category'] == 'kitchen'
    assert calls[0]['params']['min_price'] == 10
    assert calls[0]['params']['max_price'] == 200

    product = products[0]
    assert product['product_id'] == 'espresso-machine'
    assert product['price'] == pytest.approx(110.0)
    assert product['original_price'] == 100.0
    assert product['original_currency'] == 'EUR'
    assert product['retailer'] == 'shoptera_eshop.cz'


@pytest.mark.parametrize('currency,expected', [
    ('EUR', 110.0),
    ('CZK', 4.5),
    ('PLN', 25.0),
    ('USD', 100.0),
    ('GBP', 100.0),
])
def test_search_products_currency_conversion(scraper, monkeypatch, fake_response, currency, expected):
    patch_get(monkeypatch, fake_response({'results': [result(currency=currency)]}))

    assert scraper.search_products('x')[0]['price'] == pytest.approx(expected)


def test_search_products_falls_back_to_hashed_title_for_id(scraper, monkeypatch, fake_response):
    patch_get(monkeypatch, fake_response({'results': [result(product_url='')]}))

    product = scraper.search_products('x')[0]

    assert product['product_id'] == str(hash('Espresso Machine'))


def test_search_products_omits_optional_filters(scraper, monkeypatch, fake_response):
    calls = []
    patch_get(monkeypatch, fake_response({'results': []}), calls)

    scraper.search_products('x')

    assert 'category' not in calls[0]['params']
    assert 'min_price' not in calls[0]['params']
    assert 'max_price' not in calls[0]['params']


def test_search_products_handles_missing_results_key(scraper, monkeypatch, fake_response):
    patch_get(monkeypatch, fake_response({}))

    assert scraper.search_products('x') == []


def test_search_products_returns_empty_list_on_error(scraper, monkeypatch):
    patch_get(monkeypatch, requests.RequestException('timeout'))

    assert scraper.search_products('x') == []


def test_product_lookups_are_unsupported(scraper):
    assert scraper.get_product_price('1') is None
    assert scraper.get_product_info('1') == {}


def test_get_trending_products_uses_category_or_default_term(scraper, monkeypatch):
    calls = []
    monkeypatch.setattr(
        scraper, 'search_products',
        lambda term, category=None, limit=20: calls.append((term, category, limit)) or [],
    )

    scraper.get_trending_products()
    scraper.get_trending_products('kitchen', limit=5)

    assert calls == [('electronics', None, 20), ('kitchen', 'kitchen', 5)]


def test_get_categories_returns_unique_non_empty_list(scraper):
    categories = scraper.get_categories()

    assert categories
    assert len(categories) == len(set(categories))
