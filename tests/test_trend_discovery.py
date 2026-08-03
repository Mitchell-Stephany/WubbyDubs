import time

import pytest

import trend_discovery as trend_discovery_module
from trend_discovery import TrendDiscovery


class FakeDatabase:
    def __init__(self, failing_names=()):
        self.added = []
        self.failing_names = set(failing_names)

    def add_product(self, product_id, retailer, name, url, category):
        if name in self.failing_names:
            raise RuntimeError('constraint failed')
        self.added.append({
            'product_id': product_id,
            'retailer': retailer,
            'name': name,
            'url': url,
            'category': category,
        })


class TrendingScraper:
    def __init__(self, products=None, error=None):
        self.products = products or []
        self.error = error
        self.calls = []

    def get_trending_products(self, category, limit):
        self.calls.append((category, limit))
        if self.error is not None:
            raise self.error
        return self.products


class SearchOnlyScraper:
    def __init__(self, products=None):
        self.products = products or []
        self.calls = []

    def search_products(self, query, category, limit):
        self.calls.append((query, category, limit))
        return self.products


def product(name, retailer='multi_source', product_id=None):
    return {
        'product_id': product_id or f'id_{name}',
        'name': name,
        'retailer': retailer,
        'url': f'https://example.com/{name}',
        'category': 'electronics',
    }


@pytest.fixture
def db():
    return FakeDatabase()


@pytest.fixture
def discovery(config, db, monkeypatch):
    monkeypatch.setattr(trend_discovery_module.random, 'shuffle', lambda items: None)
    return TrendDiscovery(config, db)


def test_discover_trending_products_collects_from_scrapers(discovery):
    scraper = TrendingScraper([product('A'), product('B')])
    discovery.scrapers = {'multi_source': scraper}

    products = discovery.discover_trending_products()

    assert [p['name'] for p in products] == ['A', 'B']
    assert scraper.calls == [('electronics', 10)]


def test_discover_trending_products_deduplicates_by_name_and_retailer(discovery):
    duplicate = product('A')
    other_retailer = product('A', retailer='target')
    discovery.scrapers = {'multi_source': TrendingScraper([duplicate, duplicate, other_retailer])}

    products = discovery.discover_trending_products()

    assert len(products) == 2


def test_discover_trending_products_respects_max_products(discovery):
    discovery.scrapers = {'multi_source': TrendingScraper([product(f'P{i}') for i in range(10)])}

    assert len(discovery.discover_trending_products(max_products=3)) == 3


def test_discover_trending_products_skips_unconfigured_retailers(discovery):
    discovery.scrapers = {}

    assert discovery.discover_trending_products() == []


def test_discover_trending_products_falls_back_to_search(discovery, monkeypatch):
    scraper = SearchOnlyScraper([product('A')])
    discovery.scrapers = {'multi_source': scraper}
    monkeypatch.setattr(trend_discovery_module.random, 'choice', lambda options: options[0])

    products = discovery.discover_trending_products()

    assert [p['name'] for p in products] == ['A']
    assert scraper.calls == [('iPhone', 'electronics', 10)]


def test_discover_trending_products_continues_after_scraper_error(discovery):
    discovery.scrapers = {'multi_source': TrendingScraper(error=RuntimeError('blocked'))}

    assert discovery.discover_trending_products() == []


def test_discover_trending_products_sleeps_between_categories_in_advanced_mode(discovery, monkeypatch):
    discovery.config.ADVANCED_SCRAPING = True
    discovery.config.CATEGORIES = ['electronics', 'tools']
    discovery.scrapers = {'multi_source': TrendingScraper([product('A')])}
    slept = []
    monkeypatch.setattr(time, 'sleep', slept.append)

    discovery.discover_trending_products()

    assert len(slept) == 2
    assert all(2 <= seconds <= 4 for seconds in slept)


def test_get_random_search_term_uses_category_terms(discovery, monkeypatch):
    monkeypatch.setattr(trend_discovery_module.random, 'choice', lambda options: options[0])

    assert discovery._get_random_search_term('electronics') == 'iPhone'
    assert discovery._get_random_search_term('unmapped') == 'popular'


def test_deduplicate_products_is_case_insensitive(discovery):
    products = discovery._deduplicate_products([product('Widget'), product('WIDGET')])

    assert len(products) == 1


def test_add_discovered_products_writes_to_database(discovery, db):
    added = discovery.add_discovered_products([product('A'), product('B')])

    assert added == 2
    assert [p['name'] for p in db.added] == ['A', 'B']


def test_add_discovered_products_defaults_missing_fields(discovery, db):
    discovery.add_discovered_products([{'product_id': '1', 'name': 'A', 'retailer': 'multi_source'}])

    assert db.added[0]['url'] == ''
    assert db.added[0]['category'] == 'Unknown'


def test_add_discovered_products_skips_failing_rows(config):
    db = FakeDatabase(failing_names={'A'})
    discovery = TrendDiscovery(config, db)

    added = discovery.add_discovered_products([product('A'), product('B')])

    assert added == 1


def test_refresh_product_pool_discovers_then_persists(discovery, db):
    discovery.scrapers = {'multi_source': TrendingScraper([product('A')])}

    assert discovery.refresh_product_pool(max_products=5) == 1
    assert [p['name'] for p in db.added] == ['A']
