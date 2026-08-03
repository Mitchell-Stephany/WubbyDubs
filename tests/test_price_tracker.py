import asyncio

import pytest

import main
from main import PriceTracker


class FakeDatabase:
    def __init__(self, products=None):
        self.products = products or []
        self.updates = []

    def get_all_products(self):
        return self.products

    def update_price(self, product_id, price):
        self.updates.append((product_id, price))


class FakeScraper:
    def __init__(self, prices=None, error=None):
        self.prices = prices or {}
        self.error = error
        self.closed = False

    def get_product_price(self, product_id):
        if self.error is not None:
            raise self.error
        return self.prices.get(product_id)

    def close(self):
        self.closed = True


class FakeAnalyzer:
    def __init__(self, deals=None):
        self.deals = deals or []

    def analyze_all_products(self):
        return self.deals


class FakeDiscordBot:
    def __init__(self):
        self.notifications = []
        self.errors = []

    async def wait_until_ready(self):
        return None

    async def send_deal_notification(self, deal):
        if deal.get('explode'):
            raise RuntimeError('discord down')
        self.notifications.append(deal)


class FakeTrendDiscovery:
    def __init__(self, added=3, error=None):
        self.added = added
        self.error = error
        self.calls = []

    def refresh_product_pool(self, max_products):
        self.calls.append(max_products)
        if self.error is not None:
            raise self.error
        return self.added


@pytest.fixture
def tracker(config, monkeypatch):
    """PriceTracker with every collaborator replaced, skipping __init__ side effects."""
    tracker = PriceTracker.__new__(PriceTracker)
    tracker.config = config
    tracker.db = FakeDatabase()
    tracker.scrapers = {}
    tracker.price_analyzer = FakeAnalyzer()
    tracker.trend_discovery = FakeTrendDiscovery()
    tracker.discord_bot = FakeDiscordBot()
    tracker.discord_thread = None
    tracker.scheduler = main.AsyncIOScheduler()
    monkeypatch.setattr(asyncio, 'sleep', lambda seconds: asyncio.sleep(0))
    return tracker


def product(product_id='generic_0', retailer='multi_source', name='Widget'):
    return {'product_id': product_id, 'retailer': retailer, 'name': name}


async def test_check_prices_records_fetched_prices(tracker):
    tracker.db.products = [product()]
    tracker.scrapers = {'multi_source': FakeScraper({'generic_0': 12.34})}

    await tracker.check_prices()

    assert tracker.db.updates == [('generic_0', 12.34)]


async def test_check_prices_skips_products_without_matching_scraper(tracker):
    tracker.db.products = [product(retailer='walmart')]
    tracker.scrapers = {'multi_source': FakeScraper({'generic_0': 12.34})}

    await tracker.check_prices()

    assert tracker.db.updates == []


async def test_check_prices_skips_products_without_price(tracker):
    tracker.db.products = [product()]
    tracker.scrapers = {'multi_source': FakeScraper({})}

    await tracker.check_prices()

    assert tracker.db.updates == []


async def test_check_prices_continues_after_scraper_error(tracker):
    tracker.db.products = [product('a'), product('b')]
    scraper = FakeScraper(error=RuntimeError('blocked'))
    tracker.scrapers = {'multi_source': scraper}

    await tracker.check_prices()

    assert tracker.db.updates == []


async def test_analyze_and_notify_sends_each_deal(tracker):
    deals = [{'name': 'A'}, {'name': 'B'}]
    tracker.price_analyzer = FakeAnalyzer(deals)

    await tracker.analyze_and_notify()

    assert tracker.discord_bot.notifications == deals


async def test_analyze_and_notify_does_nothing_without_deals(tracker):
    await tracker.analyze_and_notify()

    assert tracker.discord_bot.notifications == []


async def test_analyze_and_notify_survives_notification_failure(tracker):
    tracker.price_analyzer = FakeAnalyzer([{'name': 'A', 'explode': True}, {'name': 'B'}])

    await tracker.analyze_and_notify()

    assert [deal['name'] for deal in tracker.discord_bot.notifications] == ['B']


async def test_discover_new_products_refreshes_pool(tracker):
    await tracker.discover_new_products()

    assert tracker.trend_discovery.calls == [30]


async def test_discover_new_products_handles_empty_result(tracker):
    tracker.trend_discovery = FakeTrendDiscovery(added=0)

    await tracker.discover_new_products()

    assert tracker.trend_discovery.calls == [30]


async def test_discover_new_products_swallows_errors(tracker):
    tracker.trend_discovery = FakeTrendDiscovery(error=RuntimeError('blocked'))

    await tracker.discover_new_products()


def test_setup_scheduler_registers_all_jobs(tracker):
    tracker.setup_scheduler()

    job_ids = {job.id for job in tracker.scheduler.get_jobs()}
    assert job_ids == {'check_prices', 'analyze_notify', 'discover_products', 'initial_discovery'}


def test_setup_scheduler_uses_configured_interval(tracker):
    tracker.config.CHECK_INTERVAL_MINUTES = 11
    tracker.setup_scheduler()

    job = tracker.scheduler.get_job('check_prices')
    assert job.trigger.interval.total_seconds() == 11 * 60


def test_start_discord_bot_runs_bot_in_background_thread(tracker, monkeypatch):
    started = asyncio.Event()

    async def fake_start_bot():
        started.set()

    tracker.discord_bot.start_bot = fake_start_bot
    monkeypatch.setattr(main.time, 'sleep', lambda seconds: None)

    tracker.start_discord_bot()
    tracker.discord_thread.join(timeout=5)

    assert tracker.discord_thread.daemon is True
    assert started.is_set()
