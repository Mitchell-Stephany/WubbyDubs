"""Tests for the error propagation added to config, database and the scrapers."""

import os
import tempfile
import unittest
from unittest import mock

import requests

import config
from database import Database
from exceptions import ConfigError, DatabaseError, ScraperError
from scrapers.shopscout import ShopScoutScraper


class ConfigErrorTests(unittest.TestCase):
    def test_invalid_channel_id_raises(self):
        with mock.patch.dict(os.environ, {'DISCORD_CHANNEL_ID': 'not-a-number'}):
            with self.assertRaises(ConfigError):
                config._channel_id()

    def test_placeholder_channel_id_is_unset(self):
        with mock.patch.dict(os.environ, {'DISCORD_CHANNEL_ID': 'your_channel_id_here'}):
            self.assertEqual(config._channel_id(), 0)

    def test_invalid_number_raises(self):
        with mock.patch.dict(os.environ, {'CHECK_INTERVAL_MINUTES': 'soon'}):
            with self.assertRaises(ConfigError):
                config._env_number('CHECK_INTERVAL_MINUTES', 5, int)


class DatabaseErrorTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.NamedTemporaryFile(suffix='.db', delete=False)
        self.tmp.close()
        self.db = Database(self.tmp.name)

    def tearDown(self):
        os.unlink(self.tmp.name)

    def test_sqlite_errors_are_wrapped(self):
        with self.assertRaises(DatabaseError):
            with self.db._connect() as conn:
                conn.execute('SELECT * FROM table_that_does_not_exist')

    def test_failed_write_is_rolled_back(self):
        self.db.add_product('p1', 'multi_source', 'Widget', 'http://example.com', 'tools')

        with self.assertRaises(DatabaseError):
            with self.db._connect() as conn:
                conn.execute('DELETE FROM products')
                conn.execute('SELECT * FROM table_that_does_not_exist')

        self.assertEqual(len(self.db.get_all_products()), 1)


class ScraperErrorTests(unittest.TestCase):
    def setUp(self):
        self.scraper = ShopScoutScraper(config.Config())

    def test_request_failure_raises_scraper_error(self):
        with mock.patch.object(
            self.scraper, '_get', side_effect=requests.ConnectionError('offline')
        ):
            with self.assertRaises(ScraperError):
                self.scraper.get_store_products('example.com')

    def test_non_json_response_raises_scraper_error(self):
        response = mock.Mock()
        response.json.side_effect = ValueError('not json')

        with mock.patch.object(self.scraper, '_get', return_value=response):
            with self.assertRaises(ScraperError):
                self.scraper.get_store_products('example.com')

    def test_unparseable_variant_price_is_none(self):
        product = {'id': 1, 'variants': [{'available': True, 'price': 'free'}]}
        self.assertIsNone(self.scraper._variant_price(product))


if __name__ == '__main__':
    unittest.main()
