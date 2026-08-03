import sqlite3

import pytest

from database import Database


@pytest.fixture
def db(tmp_path):
    return Database(str(tmp_path / 'tracker.db'))


def test_init_database_creates_tables(db):
    with sqlite3.connect(db.db_path) as conn:
        tables = {row[0] for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}

    assert {'products', 'price_history', 'deals'} <= tables


def test_init_database_is_idempotent(db):
    db.add_product('p1', 'target', 'Widget', 'https://example.com/p1')
    db.init_database()

    assert len(db.get_all_products()) == 1


def test_add_product_replaces_existing_product_id(db):
    db.add_product('p1', 'target', 'Widget', 'https://example.com/p1', 'electronics')
    db.add_product('p1', 'target', 'Widget v2', 'https://example.com/p1', 'electronics')

    products = db.get_all_products()
    assert len(products) == 1
    assert products[0]['name'] == 'Widget v2'
    assert products[0]['category'] == 'electronics'


def test_add_product_allows_null_category(db):
    db.add_product('p1', 'target', 'Widget', 'https://example.com/p1')

    assert db.get_all_products()[0]['category'] is None


def seed_history(db, product_id, prices_by_timestamp):
    """Insert history rows with explicit timestamps (CURRENT_TIMESTAMP is second-granular)."""
    with sqlite3.connect(db.db_path) as conn:
        conn.executemany(
            'INSERT INTO price_history (product_id, price, timestamp) VALUES (?, ?, ?)',
            [(product_id, price, timestamp) for timestamp, price in prices_by_timestamp],
        )


def test_latest_and_previous_price_use_most_recent_timestamps(db):
    db.add_product('p1', 'target', 'Widget', 'https://example.com/p1')
    seed_history(db, 'p1', [
        ('2024-01-01 00:00:00', 12.0),
        ('2024-01-02 00:00:00', 10.0),
        ('2024-01-03 00:00:00', 8.0),
    ])

    assert db.get_latest_price('p1') == 8.0
    assert db.get_previous_price('p1') == 10.0


def test_prices_are_none_for_unknown_product(db):
    assert db.get_latest_price('missing') is None
    assert db.get_previous_price('missing') is None


def test_update_price_appends_to_history(db):
    db.add_product('p1', 'target', 'Widget', 'https://example.com/p1')
    db.update_price('p1', 10.0)
    db.update_price('p1', 8.0)

    assert sorted(row['price'] for row in db.get_price_history('p1')) == [8.0, 10.0]


def test_previous_price_is_none_with_single_data_point(db):
    db.update_price('p1', 10.0)

    assert db.get_previous_price('p1') is None


def test_get_price_history_is_newest_first_and_limited(db):
    seed_history(db, 'p1', [
        ('2024-01-01 00:00:00', 10.0),
        ('2024-01-02 00:00:00', 9.0),
        ('2024-01-03 00:00:00', 8.0),
    ])

    history = db.get_price_history('p1', limit=2)

    assert [row['price'] for row in history] == [8.0, 9.0]
    assert all('timestamp' in row for row in history)


def test_get_price_history_is_scoped_to_product(db):
    db.update_price('p1', 10.0)
    db.update_price('p2', 20.0)

    assert [row['price'] for row in db.get_price_history('p2')] == [20.0]


def test_record_deal_persists_all_columns(db):
    db.record_deal('p1', 100.0, 60.0, 40.0, ebay_price=120.0,
                   potential_profit=30.0, profit_percentage=50.0)

    with sqlite3.connect(db.db_path) as conn:
        conn.row_factory = sqlite3.Row
        deal = dict(conn.execute('SELECT * FROM deals').fetchone())

    assert deal['original_price'] == 100.0
    assert deal['new_price'] == 60.0
    assert deal['drop_percentage'] == 40.0
    assert deal['ebay_price'] == 120.0
    assert deal['notified'] == 0


def test_record_deal_allows_missing_ebay_data(db):
    db.record_deal('p1', 100.0, 60.0, 40.0)

    with sqlite3.connect(db.db_path) as conn:
        assert conn.execute('SELECT ebay_price FROM deals').fetchone()[0] is None


def test_mark_deal_notified(db):
    db.record_deal('p1', 100.0, 60.0, 40.0)
    with sqlite3.connect(db.db_path) as conn:
        deal_id = conn.execute('SELECT id FROM deals').fetchone()[0]

    db.mark_deal_notified(deal_id)

    with sqlite3.connect(db.db_path) as conn:
        assert conn.execute('SELECT notified FROM deals').fetchone()[0] == 1


def test_get_products_by_retailer(db):
    db.add_product('p1', 'target', 'Widget', 'https://example.com/p1')
    db.add_product('p2', 'homedepot', 'Drill', 'https://example.com/p2')

    assert [p['product_id'] for p in db.get_products_by_retailer('homedepot')] == ['p2']
    assert db.get_products_by_retailer('walmart') == []


def test_update_price_refreshes_last_checked(db):
    db.add_product('p1', 'target', 'Widget', 'https://example.com/p1')
    with sqlite3.connect(db.db_path) as conn:
        conn.execute("UPDATE products SET last_checked = '2000-01-01 00:00:00' WHERE product_id = 'p1'")

    db.update_price('p1', 10.0)

    assert db.get_all_products()[0]['last_checked'] != '2000-01-01 00:00:00'
