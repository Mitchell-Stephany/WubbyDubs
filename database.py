import sqlite3
from contextlib import contextmanager
from typing import List, Dict, Optional

class Database:
    def __init__(self, db_path: str = 'price_tracker.db'):
        self.db_path = db_path
        self.init_database()
    
    @contextmanager
    def _cursor(self, as_dict: bool = False):
        """Yield a cursor and commit the transaction on success"""
        with sqlite3.connect(self.db_path) as conn:
            if as_dict:
                conn.row_factory = sqlite3.Row
            yield conn.cursor()
            conn.commit()
    
    def _execute(self, query: str, params: tuple = ()) -> Optional[int]:
        """Execute a write statement and return the inserted row id"""
        with self._cursor() as cursor:
            cursor.execute(query, params)
            return cursor.lastrowid
    
    def _fetch_one_value(self, query: str, params: tuple = ()):
        """Return the first column of the first row, if any"""
        with self._cursor() as cursor:
            cursor.execute(query, params)
            result = cursor.fetchone()
            return result[0] if result else None
    
    def _fetch_rows(self, query: str, params: tuple = ()) -> List[Dict]:
        """Return all rows as dictionaries"""
        with self._cursor(as_dict=True) as cursor:
            cursor.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]
    
    def init_database(self):
        """Initialize database tables"""
        with self._cursor() as cursor:
            # Products table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS products (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    product_id TEXT UNIQUE,
                    retailer TEXT NOT NULL,
                    name TEXT NOT NULL,
                    url TEXT,
                    category TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_checked TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Price history table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS price_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    product_id TEXT NOT NULL,
                    price REAL NOT NULL,
                    currency TEXT DEFAULT 'USD',
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (product_id) REFERENCES products(product_id)
                )
            ''')
            
            # Deals found table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS deals (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    product_id TEXT NOT NULL,
                    original_price REAL NOT NULL,
                    new_price REAL NOT NULL,
                    drop_percentage REAL NOT NULL,
                    ebay_price REAL,
                    potential_profit REAL,
                    profit_percentage REAL,
                    notified BOOLEAN DEFAULT FALSE,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (product_id) REFERENCES products(product_id)
                )
            ''')
            
            # Create indexes for performance
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_product_id ON price_history(product_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_timestamp ON price_history(timestamp)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_deals_timestamp ON deals(timestamp)')
    
    def add_product(self, product_id: str, retailer: str, name: str, 
                   url: str, category: str = None) -> int:
        """Add a new product to track"""
        return self._execute('''
            INSERT OR REPLACE INTO products 
            (product_id, retailer, name, url, category, last_checked)
            VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        ''', (product_id, retailer, name, url, category))
    
    def update_price(self, product_id: str, price: float):
        """Record a new price for a product"""
        with self._cursor() as cursor:
            cursor.execute('''
                INSERT INTO price_history (product_id, price, timestamp)
                VALUES (?, ?, CURRENT_TIMESTAMP)
            ''', (product_id, price))
            
            # Update last_checked time
            cursor.execute('''
                UPDATE products SET last_checked = CURRENT_TIMESTAMP
                WHERE product_id = ?
            ''', (product_id,))
    
    def get_latest_price(self, product_id: str) -> Optional[float]:
        """Get the most recent price for a product"""
        return self._fetch_one_value('''
            SELECT price FROM price_history
            WHERE product_id = ?
            ORDER BY timestamp DESC
            LIMIT 1
        ''', (product_id,))
    
    def get_previous_price(self, product_id: str) -> Optional[float]:
        """Get the second most recent price for comparison"""
        return self._fetch_one_value('''
            SELECT price FROM price_history
            WHERE product_id = ?
            ORDER BY timestamp DESC
            LIMIT 1 OFFSET 1
        ''', (product_id,))
    
    def get_price_history(self, product_id: str, limit: int = 100) -> List[Dict]:
        """Get price history for a product"""
        return self._fetch_rows('''
            SELECT price, timestamp FROM price_history
            WHERE product_id = ?
            ORDER BY timestamp DESC
            LIMIT ?
        ''', (product_id, limit))
    
    def record_deal(self, product_id: str, original_price: float, new_price: float,
                   drop_percentage: float, ebay_price: float = None,
                   potential_profit: float = None, profit_percentage: float = None):
        """Record a discovered deal"""
        self._execute('''
            INSERT INTO deals 
            (product_id, original_price, new_price, drop_percentage, 
             ebay_price, potential_profit, profit_percentage, notified)
            VALUES (?, ?, ?, ?, ?, ?, ?, FALSE)
        ''', (product_id, original_price, new_price, drop_percentage,
             ebay_price, potential_profit, profit_percentage))
    
    def get_all_products(self) -> List[Dict]:
        """Get all tracked products"""
        return self._fetch_rows('SELECT * FROM products')
    
    def get_products_by_retailer(self, retailer: str) -> List[Dict]:
        """Get products from a specific retailer"""
        return self._fetch_rows('SELECT * FROM products WHERE retailer = ?', (retailer,))
    
    def mark_deal_notified(self, deal_id: int):
        """Mark a deal as having been notified"""
        self._execute('UPDATE deals SET notified = TRUE WHERE id = ?', (deal_id,))
