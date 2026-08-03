import pytest

from price_analyzer import PriceAnalyzer


class FakeDatabase:
    def __init__(self, products=None, latest=None, previous=None):
        self.products = products or []
        self.latest = latest or {}
        self.previous = previous or {}
        self.recorded_deals = []

    def get_all_products(self):
        return self.products

    def get_latest_price(self, product_id):
        return self.latest.get(product_id)

    def get_previous_price(self, product_id):
        return self.previous.get(product_id)

    def record_deal(self, **kwargs):
        self.recorded_deals.append(kwargs)


class FakeEbay:
    def __init__(self, enabled=True, average_price=None, profit=None):
        self.enabled = enabled
        self.average_price = average_price
        self.profit = profit or {'profit': 0, 'profit_percentage': 0, 'profitable': False}

    def get_average_price(self, name):
        return self.average_price

    def calculate_potential_profit(self, retail_price, ebay_price):
        return self.profit


def product(product_id='p1'):
    return {
        'product_id': product_id,
        'name': 'Wireless Earbuds',
        'retailer': 'multi_source',
        'url': 'https://example.com/p1',
        'category': 'electronics',
    }


def analyzer(config, db, ebay):
    return PriceAnalyzer(config, db, ebay)


def test_analyze_price_change_returns_none_without_previous_price(config):
    db = FakeDatabase(products=[product()])

    assert analyzer(config, db, FakeEbay()).analyze_price_change('p1', 50.0) is None


def test_analyze_price_change_returns_none_when_price_rose(config):
    db = FakeDatabase(products=[product()], previous={'p1': 40.0})

    assert analyzer(config, db, FakeEbay()).analyze_price_change('p1', 50.0) is None


def test_analyze_price_change_returns_none_for_unknown_product(config):
    db = FakeDatabase(products=[], previous={'p1': 100.0})

    assert analyzer(config, db, FakeEbay()).analyze_price_change('p1', 50.0) is None


def test_analyze_price_change_treats_zero_previous_price_as_no_drop(config):
    db = FakeDatabase(products=[product()], previous={'p1': 0.0})

    assert analyzer(config, db, FakeEbay()).analyze_price_change('p1', 50.0) is None


def test_analyze_price_change_reports_profitable_deal(config):
    db = FakeDatabase(products=[product()], previous={'p1': 100.0})
    ebay = FakeEbay(
        average_price=150.0,
        profit={'profit': 20.0, 'profit_percentage': 25.0, 'profitable': True},
    )

    deal = analyzer(config, db, ebay).analyze_price_change('p1', 90.0)

    assert deal['drop_percentage'] == pytest.approx(10.0)
    assert deal['ebay_price'] == 150.0
    assert deal['potential_profit'] == 20.0
    assert deal['is_good_deal'] is True
    assert deal['fallback_mode'] is False
    assert db.recorded_deals[0]['product_id'] == 'p1'


def test_analyze_price_change_flags_large_drop_even_when_unprofitable(config):
    db = FakeDatabase(products=[product()], previous={'p1': 100.0})
    ebay = FakeEbay(average_price=110.0)

    deal = analyzer(config, db, ebay).analyze_price_change('p1', 60.0)

    assert deal['is_good_deal'] is True


def test_analyze_price_change_ignores_small_unprofitable_drop(config):
    db = FakeDatabase(products=[product()], previous={'p1': 100.0})
    ebay = FakeEbay(average_price=110.0)

    assert analyzer(config, db, ebay).analyze_price_change('p1', 95.0) is None
    assert db.recorded_deals == []


def test_analyze_price_change_uses_drop_threshold_in_fallback_mode(config):
    db = FakeDatabase(products=[product()], previous={'p1': 100.0})
    ebay = FakeEbay(enabled=False)

    deal = analyzer(config, db, ebay).analyze_price_change('p1', 80.0)

    assert deal['fallback_mode'] is True
    assert deal['ebay_price'] is None
    assert deal['potential_profit'] == 0


def test_analyze_price_change_below_fallback_threshold(config):
    db = FakeDatabase(products=[product()], previous={'p1': 100.0})
    ebay = FakeEbay(enabled=False)

    assert analyzer(config, db, ebay).analyze_price_change('p1', 90.0) is None


def test_analyze_all_products_collects_deals(config):
    db = FakeDatabase(
        products=[product('p1'), product('p2')],
        latest={'p1': 50.0, 'p2': 50.0},
        previous={'p1': 100.0},
    )
    ebay = FakeEbay(enabled=False)

    deals = analyzer(config, db, ebay).analyze_all_products()

    assert [deal['product_id'] for deal in deals] == ['p1']


def test_analyze_all_products_skips_products_without_current_price(config):
    db = FakeDatabase(products=[product()], latest={}, previous={'p1': 100.0})

    assert analyzer(config, db, FakeEbay(enabled=False)).analyze_all_products() == []


def test_get_significant_drops_filters_by_threshold(config):
    db = FakeDatabase(
        products=[product('p1'), product('p2')],
        latest={'p1': 50.0, 'p2': 95.0},
        previous={'p1': 100.0, 'p2': 100.0},
    )

    drops = analyzer(config, db, FakeEbay()).get_significant_drops(min_drop_percentage=20)

    assert [drop['product_id'] for drop in drops] == ['p1']
    assert drops[0]['drop_percentage'] == pytest.approx(50.0)


def test_get_significant_drops_ignores_incomplete_history(config):
    db = FakeDatabase(
        products=[product('p1'), product('p2')],
        latest={'p1': 50.0},
        previous={'p2': 0.0},
    )

    assert analyzer(config, db, FakeEbay()).get_significant_drops() == []
