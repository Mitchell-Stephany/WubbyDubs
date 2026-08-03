import pytest

import scrapers.advanced_base as advanced_base
from scrapers.advanced_base import AdvancedScraper
from scrapers.advanced_homedepot import AdvancedHomeDepotScraper
from scrapers.advanced_target import AdvancedTargetScraper


class FakeElement:
    def __init__(self, text='', attributes=None, children=None):
        self.text = text
        self._attributes = attributes or {}
        self._children = children or {}

    def get_attribute(self, name):
        return self._attributes.get(name)

    def find_element(self, by, selector):
        if selector not in self._children:
            raise LookupError(selector)
        return self._children[selector]

    def clear(self):
        pass

    def send_keys(self, value):
        pass

    def submit(self):
        pass


class FakeDriver:
    def __init__(self, elements=None):
        self.visited = []
        self.elements = elements or {}

    def get(self, url):
        self.visited.append(url)

    def find_elements(self, by, selector):
        return self.elements.get(selector, [])

    def quit(self):
        pass


@pytest.fixture(autouse=True)
def no_driver_launch(monkeypatch):
    monkeypatch.setattr(AdvancedScraper, '_init_driver', lambda self: setattr(self, 'driver', None))
    monkeypatch.setattr(advanced_base.time, 'sleep', lambda seconds: None)


@pytest.fixture(params=[AdvancedTargetScraper, AdvancedHomeDepotScraper])
def scraper_class(request):
    return request.param


def make(scraper_class, config, driver):
    scraper = scraper_class(config)
    scraper.driver = driver
    return scraper


def stub_text(scraper, monkeypatch, values):
    """Return canned text per CSS/XPath selector, None for anything else."""
    monkeypatch.setattr(
        scraper, '_safe_get_element_text',
        lambda by, selector, timeout=10: values.get(selector),
    )


def test_methods_short_circuit_without_driver(scraper_class, config):
    scraper = scraper_class(config)

    assert scraper.get_product_price('1') is None
    assert scraper.get_product_info('1') == {}
    assert scraper.search_products('drill') == []


def test_get_product_price_parses_first_matching_selector(scraper_class, config, monkeypatch):
    driver = FakeDriver()
    scraper = make(scraper_class, config, driver)
    selector = '[data-test="product-price"]' if scraper_class is AdvancedTargetScraper else '[data-testid="product-price"]'
    stub_text(scraper, monkeypatch, {selector: ' $1,234.56 '})

    assert scraper.get_product_price('999') == 1234.56
    assert driver.visited == [f'{scraper.BASE_URL}/p/999']


def test_get_product_price_skips_unparseable_text(scraper_class, config, monkeypatch):
    scraper = make(scraper_class, config, FakeDriver())
    fallback = '.Price-characteristic' if scraper_class is AdvancedTargetScraper else '.price__format'
    first = '[data-test="product-price"]' if scraper_class is AdvancedTargetScraper else '[data-testid="product-price"]'
    stub_text(scraper, monkeypatch, {first: 'See price in cart', fallback: '42.00'})

    assert scraper.get_product_price('999') == 42.00


def test_get_product_price_returns_none_when_no_selector_matches(scraper_class, config, monkeypatch):
    scraper = make(scraper_class, config, FakeDriver())
    stub_text(scraper, monkeypatch, {})

    assert scraper.get_product_price('999') is None


def test_get_product_price_returns_none_on_driver_error(scraper_class, config, monkeypatch):
    scraper = make(scraper_class, config, FakeDriver())
    monkeypatch.setattr(scraper.driver, 'get', lambda url: (_ for _ in ()).throw(RuntimeError('crash')))

    assert scraper.get_product_price('999') is None


def test_get_product_info_collects_name_price_and_breadcrumb(scraper_class, config, monkeypatch):
    breadcrumb_selector = (
        '[data-test="breadcrumb"] a' if scraper_class is AdvancedTargetScraper else '.breadcrumb a'
    )
    title_selector = (
        '[data-test="product-title"]' if scraper_class is AdvancedTargetScraper else 'h1.product-title'
    )
    driver = FakeDriver({breadcrumb_selector: [FakeElement('Tools'), FakeElement(' Power Tools ')]})
    scraper = make(scraper_class, config, driver)
    stub_text(scraper, monkeypatch, {title_selector: 'Cordless Drill'})
    monkeypatch.setattr(scraper, 'get_product_price', lambda product_id: 59.99)

    info = scraper.get_product_info('999')

    assert info['name'] == 'Cordless Drill'
    assert info['category'] == 'Power Tools'
    assert info['price'] == 59.99
    assert info['url'] == f'{scraper.BASE_URL}/p/999'


def test_get_product_info_falls_back_to_h1_and_unknown_category(scraper_class, config, monkeypatch):
    scraper = make(scraper_class, config, FakeDriver())
    stub_text(scraper, monkeypatch, {'h1': 'Fallback Title'})
    monkeypatch.setattr(scraper, 'get_product_price', lambda product_id: None)

    info = scraper.get_product_info('999')

    assert info['name'] == 'Fallback Title'
    assert info['category'] == 'Unknown'


def test_get_product_info_defaults_name_to_unknown(scraper_class, config, monkeypatch):
    scraper = make(scraper_class, config, FakeDriver())
    stub_text(scraper, monkeypatch, {})
    monkeypatch.setattr(scraper, 'get_product_price', lambda product_id: None)

    assert scraper.get_product_info('999')['name'] == 'Unknown'


def test_get_product_info_returns_empty_dict_on_driver_error(scraper_class, config, monkeypatch):
    scraper = make(scraper_class, config, FakeDriver())
    monkeypatch.setattr(scraper.driver, 'get', lambda url: (_ for _ in ()).throw(RuntimeError('crash')))

    assert scraper.get_product_info('999') == {}


def test_get_trending_products_maps_category_to_search_term(scraper_class, config, monkeypatch):
    scraper = make(scraper_class, config, FakeDriver())
    calls = []
    monkeypatch.setattr(
        scraper, 'search_products',
        lambda term, category=None, limit=20: calls.append((term, category, limit)) or [],
    )

    scraper.get_trending_products()
    scraper.get_trending_products('kitchen', limit=3)

    default_term = 'electronics' if scraper_class is AdvancedTargetScraper else 'tools'
    assert calls == [(default_term, 'all', 20), ('kitchen', 'kitchen', 3)]


def test_target_search_products_parses_cards(config, monkeypatch):
    card = FakeElement(
        attributes={'data-tcin': '111'},
        children={
            '[data-test="product-title"]': FakeElement(' Wireless Earbuds '),
            '[data-test="product-price"]': FakeElement('$19.99'),
            'a[href*="/p/"]': FakeElement(attributes={'href': '/p/A-111'}),
        },
    )
    card_without_tcin = FakeElement(attributes={})
    driver = FakeDriver({'[data-test="product-card"]': [card, card_without_tcin]})
    scraper = make(AdvancedTargetScraper, config, driver)
    monkeypatch.setattr(
        'scrapers.advanced_target.WebDriverWait.until',
        lambda self, condition: FakeElement(),
    )

    products = scraper.search_products('earbuds', category='electronics', limit=5)

    assert len(products) == 1
    assert products[0]['product_id'] == '111'
    assert products[0]['name'] == 'Wireless Earbuds'
    assert products[0]['price'] == 19.99
    assert products[0]['retailer'] == 'target'


def test_target_search_products_returns_empty_list_on_error(config, monkeypatch):
    scraper = make(AdvancedTargetScraper, config, FakeDriver())
    monkeypatch.setattr(scraper.driver, 'get', lambda url: (_ for _ in ()).throw(RuntimeError('crash')))

    assert scraper.search_products('earbuds') == []


def test_homedepot_search_products_parses_cards(config):
    card = FakeElement(children={
        'a.product-pod__link': FakeElement(attributes={'href': '/p/305626551'}),
        '.product-pod__title': FakeElement(' Cordless Drill '),
        '.price__format': FakeElement('$99.00'),
    })
    card_without_product_url = FakeElement(children={
        'a.product-pod__link': FakeElement(attributes={'href': '/b/category'}),
    })
    driver = FakeDriver({'.product-pod': [card, card_without_product_url]})
    scraper = make(AdvancedHomeDepotScraper, config, driver)

    products = scraper.search_products('drill', category='tools', limit=5)

    assert len(products) == 1
    assert products[0]['product_id'] == '305626551'
    assert products[0]['name'] == 'Cordless Drill'
    assert products[0]['price'] == 99.00
    assert products[0]['retailer'] == 'homedepot'
    assert driver.visited == ['https://www.homedepot.com/s/drill']


def test_homedepot_search_products_returns_empty_list_on_error(config, monkeypatch):
    scraper = make(AdvancedHomeDepotScraper, config, FakeDriver())
    monkeypatch.setattr(scraper.driver, 'get', lambda url: (_ for _ in ()).throw(RuntimeError('crash')))

    assert scraper.search_products('drill') == []
