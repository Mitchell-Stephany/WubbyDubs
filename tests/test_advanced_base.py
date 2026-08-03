import pytest
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By

import scrapers.advanced_base as advanced_base
from scrapers.advanced_base import AdvancedScraper


class DummyScraper(AdvancedScraper):
    def get_product_price(self, product_id):
        return None

    def get_product_info(self, product_id):
        return {}

    def search_products(self, query, category=None):
        return []


@pytest.fixture
def scraper(config, monkeypatch):
    monkeypatch.setattr(AdvancedScraper, '_init_driver', lambda self: setattr(self, 'driver', None))
    monkeypatch.setattr(advanced_base.time, 'sleep', lambda seconds: None)
    return DummyScraper(config)


class FakeDriver:
    def __init__(self):
        self.quit_calls = 0

    def quit(self):
        self.quit_calls += 1


def test_random_headers_include_rotating_user_agent(scraper):
    headers = scraper._random_headers()

    assert headers['User-Agent']
    assert headers['Accept-Language'] == 'en-US,en;q=0.5'
    assert headers['Sec-Fetch-Mode'] == 'navigate'


def test_random_delay_sleeps_within_bounds(scraper, monkeypatch):
    slept = []
    monkeypatch.setattr(advanced_base.time, 'sleep', slept.append)

    scraper._random_delay(1, 2)

    assert 1 <= slept[0] <= 2


def test_safe_get_element_text_strips_whitespace(scraper, monkeypatch):
    class FakeElement:
        text = '  $19.99  '

    monkeypatch.setattr(
        advanced_base.WebDriverWait, 'until',
        lambda self, condition: FakeElement(),
    )

    assert scraper._safe_get_element_text(By.CSS_SELECTOR, '.price') == '$19.99'


def test_safe_get_element_text_returns_none_on_timeout(scraper, monkeypatch):
    def timeout(self, condition):
        raise TimeoutException()

    monkeypatch.setattr(advanced_base.WebDriverWait, 'until', timeout)

    assert scraper._safe_get_element_text(By.CSS_SELECTOR, '.price') is None


def test_safe_get_element_attribute_returns_value(scraper, monkeypatch):
    class FakeElement:
        def get_attribute(self, name):
            return f'value-of-{name}'

    monkeypatch.setattr(
        advanced_base.WebDriverWait, 'until',
        lambda self, condition: FakeElement(),
    )

    assert scraper._safe_get_element_attribute(By.CSS_SELECTOR, 'a', 'href') == 'value-of-href'


def test_safe_get_element_attribute_returns_none_on_timeout(scraper, monkeypatch):
    def timeout(self, condition):
        raise TimeoutException()

    monkeypatch.setattr(advanced_base.WebDriverWait, 'until', timeout)

    assert scraper._safe_get_element_attribute(By.CSS_SELECTOR, 'a', 'href') is None


def test_close_quits_driver_once_available(scraper):
    driver = FakeDriver()
    scraper.driver = driver

    scraper.close()

    assert driver.quit_calls == 1


def test_close_is_a_noop_without_driver(scraper):
    scraper.close()


def test_init_driver_disables_scraper_when_chrome_unavailable(config, monkeypatch):
    monkeypatch.setattr(
        advanced_base.ChromeDriverManager, 'install',
        lambda self: (_ for _ in ()).throw(RuntimeError('no chrome')),
    )

    assert DummyScraper(config).driver is None
