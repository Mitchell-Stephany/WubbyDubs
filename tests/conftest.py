import os
import sys
from types import SimpleNamespace

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class FakeResponse:
    """Minimal stand-in for requests.Response."""

    def __init__(self, json_data=None, text='', status_code=200, raise_error=None):
        self._json_data = json_data
        self.text = text
        self.status_code = status_code
        self._raise_error = raise_error

    def json(self):
        if self._json_data is None:
            raise ValueError('No JSON object could be decoded')
        return self._json_data

    def raise_for_status(self):
        if self._raise_error is not None:
            raise self._raise_error


@pytest.fixture
def fake_response():
    return FakeResponse


@pytest.fixture
def config():
    """Config-like object with the attributes the modules under test read."""
    return SimpleNamespace(
        DISCORD_BOT_TOKEN='token',
        DISCORD_CHANNEL_ID=1234,
        EBAY_APP_ID='app',
        EBAY_CERT_ID='cert',
        EBAY_DEV_ID='dev',
        EBAY_ENABLED=True,
        BEST_BUY_API_KEY='bb-key',
        BEST_BUY_ENABLED=True,
        CHECK_INTERVAL_MINUTES=5,
        MIN_PROFIT_PERCENTAGE=15.0,
        EBAY_FEE_PERCENTAGE=13.0,
        RETAILERS=['multi_source'],
        CATEGORIES=['electronics'],
        SHOPIFY_STORES=['example.com'],
        FALLBACK_MODE=False,
        ADVANCED_SCRAPING=False,
    )


@pytest.fixture(autouse=True)
def stub_user_agent(monkeypatch):
    """Keep fake_useragent from touching the network during scraper construction."""
    monkeypatch.setattr(
        'fake_useragent.UserAgent.random',
        property(lambda self: 'Mozilla/5.0 (test)'),
        raising=False,
    )
