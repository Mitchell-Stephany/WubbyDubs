import dataclasses

import pytest
from ebaysdk.exception import ConnectionError as EbayConnectionError

import ebay_api
from ebay_api import eBayAPI


class FakeApi:
    """Stand-in for ebaysdk Finding connection."""

    def __init__(self, payload=None, error=None):
        self.payload = payload if payload is not None else {}
        self.error = error
        self.calls = []

    def execute(self, operation, params):
        self.calls.append((operation, params))
        if self.error is not None:
            raise self.error
        return FakeResponse(self.payload)


@dataclasses.dataclass
class FakeResponse:
    payload: dict

    def dict(self):
        return self.payload


def items_payload(*items):
    return {'searchResult': {'item': list(items)}}


def item(price, title='Item', currency='USD'):
    return {
        'title': title,
        'sellingStatus': {'currentPrice': {'value': price, '_currencyId': currency}},
        'listingInfo': {'endTime': '2024-01-01T00:00:00.000Z'},
        'viewItemURL': 'https://ebay.com/itm/1',
        'condition': {'conditionDisplayName': 'New'},
    }


@pytest.fixture
def enabled_api(config, monkeypatch):
    monkeypatch.setattr(ebay_api, 'Finding', lambda **kwargs: FakeApi())
    return eBayAPI(config)


@pytest.fixture
def disabled_api(config):
    config.EBAY_ENABLED = False
    return eBayAPI(config)


def test_init_disables_api_when_connection_fails(config, monkeypatch):
    def boom(**kwargs):
        raise RuntimeError('bad credentials')

    monkeypatch.setattr(ebay_api, 'Finding', boom)

    api = eBayAPI(config)

    assert api.enabled is False


def test_init_skips_connection_when_not_configured(disabled_api):
    assert disabled_api.enabled is False
    assert disabled_api.api is None


def test_get_average_price_averages_valid_prices(enabled_api):
    enabled_api.api.payload = items_payload(item('100.00'), item('200.00'), item('0'))

    assert enabled_api.get_average_price('switch') == 150.0
    operation, params = enabled_api.api.calls[0]
    assert operation == 'findCompletedItems'
    assert params['keywords'] == 'switch'


def test_get_average_price_skips_unparseable_prices(enabled_api):
    enabled_api.api.payload = items_payload(item('abc'), item('50.00'))

    assert enabled_api.get_average_price('switch') == 50.0


def test_get_average_price_returns_none_without_items(enabled_api):
    enabled_api.api.payload = items_payload()

    assert enabled_api.get_average_price('switch') is None


def test_get_average_price_returns_none_when_no_valid_prices(enabled_api):
    enabled_api.api.payload = items_payload(item('0'))

    assert enabled_api.get_average_price('switch') is None


def test_get_average_price_returns_none_when_disabled(disabled_api):
    assert disabled_api.get_average_price('switch') is None


@pytest.mark.parametrize('error', [EbayConnectionError('down'), RuntimeError('boom')])
def test_get_average_price_returns_none_on_error(enabled_api, error):
    enabled_api.api.error = error

    assert enabled_api.get_average_price('switch') is None


def test_get_sold_listings_maps_fields(enabled_api):
    enabled_api.api.payload = items_payload(item('99.99', title='Switch'))

    listings = enabled_api.get_sold_listings('switch', limit=5)

    assert listings == [{
        'title': 'Switch',
        'price': 99.99,
        'currency': 'USD',
        'end_time': '2024-01-01T00:00:00.000Z',
        'url': 'https://ebay.com/itm/1',
        'condition': 'New',
    }]
    assert enabled_api.api.calls[0][1]['paginationInput']['entriesPerPage'] == 5


def test_get_sold_listings_returns_empty_when_disabled(disabled_api):
    assert disabled_api.get_sold_listings('switch') == []


@pytest.mark.parametrize('error', [EbayConnectionError('down'), RuntimeError('boom')])
def test_get_sold_listings_returns_empty_on_error(enabled_api, error):
    enabled_api.api.error = error

    assert enabled_api.get_sold_listings('switch') == []


def test_get_current_listings_uses_advanced_search(enabled_api):
    enabled_api.api.payload = items_payload(item('42.00', title='Switch'))

    listings = enabled_api.get_current_listings('switch')

    assert enabled_api.api.calls[0][0] == 'findItemsAdvanced'
    assert listings[0]['price'] == 42.00
    assert 'end_time' not in listings[0]


def test_get_current_listings_returns_empty_when_disabled(disabled_api):
    assert disabled_api.get_current_listings('switch') == []


@pytest.mark.parametrize('error', [EbayConnectionError('down'), RuntimeError('boom')])
def test_get_current_listings_returns_empty_on_error(enabled_api, error):
    enabled_api.api.error = error

    assert enabled_api.get_current_listings('switch') == []


def test_calculate_potential_profit_for_profitable_deal(enabled_api):
    result = enabled_api.calculate_potential_profit(retail_price=100.0, ebay_price=200.0)

    assert result['ebay_fee'] == pytest.approx(26.0)
    assert result['shipping_cost'] == 15.0
    assert result['total_cost'] == pytest.approx(141.0)
    assert result['profit'] == pytest.approx(59.0)
    assert result['profit_percentage'] == pytest.approx(59.0)
    assert result['profitable'] is True
    assert result['requires_ebay'] is False


def test_calculate_potential_profit_below_threshold_is_not_profitable(enabled_api):
    result = enabled_api.calculate_potential_profit(retail_price=100.0, ebay_price=125.0)

    assert result['profit'] < 0
    assert result['profitable'] is False


@pytest.mark.parametrize('ebay_price', [None, 0, 50.0])
def test_calculate_potential_profit_without_upside(enabled_api, ebay_price):
    result = enabled_api.calculate_potential_profit(retail_price=100.0, ebay_price=ebay_price)

    assert result == {
        'profit': 0,
        'profit_percentage': 0,
        'ebay_fee': 0,
        'profitable': False,
        'requires_ebay': True,
    }


def test_calculate_potential_profit_when_disabled(disabled_api):
    assert disabled_api.calculate_potential_profit(10.0, 100.0)['requires_ebay'] is True


def test_calculate_potential_profit_handles_zero_retail_price(enabled_api):
    result = enabled_api.calculate_potential_profit(retail_price=0.0, ebay_price=100.0)

    assert result['profit_percentage'] == 0
