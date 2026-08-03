import pytest

import scrapers.multi_source as multi_source_module
from scrapers.base import BaseScraper
from scrapers.multi_source import MultiSourceScraper


@pytest.fixture
def scraper(config):
    return MultiSourceScraper(config)


@pytest.fixture
def no_price_jitter(monkeypatch):
    """Pin randomness so generated prices and price walks are deterministic."""
    monkeypatch.setattr(multi_source_module.random, 'uniform', lambda low, high: low)
    monkeypatch.setattr(multi_source_module.random, 'random', lambda: 1.0)


def test_base_headers_include_random_user_agent(scraper):
    headers = scraper._get_headers()

    assert headers['User-Agent']
    assert headers['Accept-Language'] == 'en-US,en;q=0.5'


def test_base_scraper_cannot_be_instantiated(config):
    with pytest.raises(TypeError):
        BaseScraper(config)


def test_get_product_price_returns_none_for_foreign_ids(scraper):
    assert scraper.get_product_price('target_12345') is None


def test_get_product_price_initializes_and_caches_price(scraper, no_price_jitter):
    price = scraper.get_product_price('generic_electronics_0')

    assert price == 10.0
    assert scraper.get_product_price('generic_electronics_0') == 10.0


def test_get_product_price_applies_simulated_drop(scraper, monkeypatch):
    monkeypatch.setattr(multi_source_module.random, 'uniform', lambda low, high: low)
    monkeypatch.setattr(multi_source_module.random, 'random', lambda: 0.0)

    price = scraper.get_product_price('generic_electronics_0')

    assert price == pytest.approx(7.0)


def test_get_product_info_is_not_supported(scraper):
    assert scraper.get_product_info('generic_electronics_0') == {}


def test_search_products_returns_catalog_entries(scraper, no_price_jitter):
    products = scraper.search_products('earbuds')

    assert products
    assert all(p['retailer'] == 'multi_source' for p in products)
    assert all(p['product_id'].startswith('generic_electronics_') for p in products)
    assert products[0]['name'].endswith('Earbuds')


@pytest.mark.parametrize('query,expected_category', [
    ('bath towels for home', 'home'),
    ('cordless drill and wrench', 'tools'),
    ('chef knife for cooking', 'kitchen'),
    ('kitchen gadgets', 'home'),
    ('bluetooth speaker', 'electronics'),
])
def test_catalog_category_is_inferred_from_query(scraper, no_price_jitter, query, expected_category):
    products = scraper.search_products(query)

    assert products[0]['category'] == expected_category


def test_explicit_category_overrides_query_inference(scraper, no_price_jitter):
    products = scraper.search_products('cordless drill', category='kitchen')

    assert products[0]['category'] == 'kitchen'


def test_unknown_category_falls_back_to_electronics(scraper, no_price_jitter):
    products = scraper.search_products('', category='automotive')

    assert products[0]['category'] == 'electronics'
    assert products[0]['name'].endswith('Popular')


def test_get_trending_products_respects_limit(scraper, no_price_jitter):
    products = scraper.get_trending_products('tools', limit=3)

    assert len(products) == 3
    assert all(p['category'] == 'tools' for p in products)


def test_get_trending_products_picks_random_query_for_all(scraper, no_price_jitter, monkeypatch):
    monkeypatch.setattr(multi_source_module.random, 'choice', lambda options: 'tools')

    products = scraper.get_trending_products()

    assert products[0]['category'] == 'tools'


def test_catalog_seeds_price_tracking_state(scraper, no_price_jitter):
    products = scraper.search_products('earbuds')

    product_id = products[0]['product_id']
    assert scraper.product_prices[product_id] == products[0]['price']
