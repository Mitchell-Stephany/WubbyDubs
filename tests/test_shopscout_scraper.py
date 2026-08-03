import pytest
import requests

from scrapers.shopscout import ShopScoutScraper


@pytest.fixture
def scraper(config):
    return ShopScoutScraper(config)


STORE_PAYLOAD = {
    'products': [
        {
            'id': 100,
            'title': 'Hoodie',
            'handle': 'hoodie',
            'body_html': '<p>Warm</p>',
            'vendor': 'Gymshark',
            'product_type': 'Apparel',
            'tags': 'sale',
            'images': [{'src': 'https://img/1.jpg'}, {'src': 'https://img/2.jpg'}],
            'variants': [
                {'available': False, 'price': '10.00'},
                {'available': True, 'price': '25.50'},
            ],
        },
        {
            'id': 200,
            'title': 'Sold Out Tee',
            'handle': 'tee',
            'images': [],
            'variants': [{'available': False, 'price': '15.00'}],
        },
        {
            'id': 300,
            'title': 'No Variants',
            'handle': 'none',
            'images': [],
            'variants': [],
        },
    ]
}


def patch_get(monkeypatch, response, recorder=None):
    def fake_get(url, headers=None, timeout=None, **kwargs):
        if recorder is not None:
            recorder.append({'url': url, 'timeout': timeout})
        if isinstance(response, Exception):
            raise response
        return response

    monkeypatch.setattr(requests, 'get', fake_get)


def test_get_store_products_maps_products(scraper, monkeypatch, fake_response):
    calls = []
    patch_get(monkeypatch, fake_response(STORE_PAYLOAD), calls)

    products = scraper.get_store_products('gymshark.com')

    assert calls[0]['url'] == 'https://gymshark.com/products.json'
    assert [p['product_id'] for p in products] == ['100', '200', '300']
    assert products[0]['price'] == 25.50
    assert products[0]['url'] == 'https://gymshark.com/products/hoodie'
    assert products[0]['retailer'] == 'shopify_gymshark.com'
    assert products[0]['images'] == ['https://img/1.jpg', 'https://img/2.jpg']


def test_get_store_products_falls_back_to_first_variant_price(scraper, monkeypatch, fake_response):
    patch_get(monkeypatch, fake_response(STORE_PAYLOAD))

    products = scraper.get_store_products('gymshark.com')

    assert products[1]['price'] == 15.00


def test_get_store_products_leaves_price_none_without_variants(scraper, monkeypatch, fake_response):
    patch_get(monkeypatch, fake_response(STORE_PAYLOAD))

    assert scraper.get_store_products('gymshark.com')[2]['price'] is None


def test_get_store_products_returns_empty_list_on_error(scraper, monkeypatch):
    patch_get(monkeypatch, requests.RequestException('403'))

    assert scraper.get_store_products('gymshark.com') == []


def test_get_product_price_finds_available_variant(scraper, monkeypatch, fake_response):
    patch_get(monkeypatch, fake_response(STORE_PAYLOAD))

    assert scraper.get_product_price('100', 'gymshark.com') == 25.50


def test_get_product_price_falls_back_to_first_variant(scraper, monkeypatch, fake_response):
    patch_get(monkeypatch, fake_response(STORE_PAYLOAD))

    assert scraper.get_product_price('200', 'gymshark.com') == 15.00


def test_get_product_price_returns_none_for_unknown_product(scraper, monkeypatch, fake_response):
    patch_get(monkeypatch, fake_response(STORE_PAYLOAD))

    assert scraper.get_product_price('999', 'gymshark.com') is None


def test_get_product_price_returns_none_on_error(scraper, monkeypatch):
    patch_get(monkeypatch, requests.RequestException('403'))

    assert scraper.get_product_price('100', 'gymshark.com') is None


def test_get_product_info_returns_full_details(scraper, monkeypatch, fake_response):
    patch_get(monkeypatch, fake_response(STORE_PAYLOAD))

    info = scraper.get_product_info('100', 'gymshark.com')

    assert info['name'] == 'Hoodie'
    assert info['price'] == 25.50
    assert info['vendor'] == 'Gymshark'
    assert info['product_type'] == 'Apparel'
    assert info['tags'] == 'sale'
    assert info['category'] == 'Unknown'


def test_get_product_info_returns_empty_dict_for_unknown_product(scraper, monkeypatch, fake_response):
    patch_get(monkeypatch, fake_response(STORE_PAYLOAD))

    assert scraper.get_product_info('999', 'gymshark.com') == {}


def test_get_product_info_returns_empty_dict_on_error(scraper, monkeypatch):
    patch_get(monkeypatch, requests.RequestException('403'))

    assert scraper.get_product_info('100', 'gymshark.com') == {}


def test_search_products_requires_domain(scraper, monkeypatch, fake_response):
    patch_get(monkeypatch, fake_response(STORE_PAYLOAD))

    assert scraper.search_products('hoodie') == []
    assert len(scraper.search_products('hoodie', 'gymshark.com')) == 3


def test_get_trending_products_requires_domain(scraper, monkeypatch, fake_response):
    patch_get(monkeypatch, fake_response(STORE_PAYLOAD))

    assert scraper.get_trending_products() == []
    assert len(scraper.get_trending_products('gymshark.com')) == 3


def test_get_popular_shopify_stores_returns_unique_domains(scraper):
    stores = scraper.get_popular_shopify_stores()

    assert stores
    assert len(stores) == len(set(stores))
    assert all('.' in domain and '/' not in domain for domain in stores)
