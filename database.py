import sqlite3
from datetime import datetime
from typing import List, Dict, Optional
import json

class Database:
    def __init__(self, db_path: str = 'price_tracker.db'):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize database tables"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
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
            
            conn.commit()
    
    def add_product(self, product_id: str, retailer: str, name: str, 
                   url: str, category: str = None) -> int:
        """Add a new product to track"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO products 
                (product_id, retailer, name, url, category, last_checked)
                VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            ''', (product_id, retailer, name, url, category))
            conn.commit()
            return cursor.lastrowid
    
    def update_price(self, product_id: str, price: float):
        """Record a new price for a product"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO price_history (product_id, price, timestamp)
                VALUES (?, ?, CURRENT_TIMESTAMP)
            ''', (product_id, price))
            
            # Update last_checked time
            cursor.execute('''
                UPDATE products SET last_checked = CURRENT_TIMESTAMP
                WHERE product_id = ?
            ''', (product_id,))
            
            conn.commit()
    
    def get_latest_price(self, product_id: str) -> Optional[float]:
        """Get the most recent price for a product"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT price FROM price_history
                WHERE product_id = ?
                ORDER BY timestamp DESC
                LIMIT 1
            ''', (product_id,))
            result = cursor.fetchone()
            return result[0] if result else None
    
    def get_previous_price(self, product_id: str) -> Optional[float]:
        """Get the second most recent price for comparison"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT price FROM price_history
                WHERE product_id = ?
                ORDER BY timestamp DESC
                LIMIT 1 OFFSET 1
            ''', (product_id,))
            result = cursor.fetchone()
            return result[0] if result else None
    
    def get_price_history(self, product_id: str, limit: int = 100) -> List[Dict]:
        """Get price history for a product"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute('''
                SELECT price, timestamp FROM price_history
                WHERE product_id = ?
                ORDER BY timestamp DESC
                LIMIT ?
            ''', (product_id, limit))
            return [dict(row) for row in cursor.fetchall()]
    
    def record_deal(self, product_id: str, original_price: float, new_price: float,
                   drop_percentage: float, ebay_price: float = None,
                   potential_profit: float = None, profit_percentage: float = None):
        """Record a discovered deal"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO deals 
                (product_id, original_price, new_price, drop_percentage, 
                 ebay_price, potential_profit, profit_percentage, notified)
                VALUES (?, ?, ?, ?, ?, ?, ?, FALSE)
            ''', (product_id, original_price, new_price, drop_percentage,
                 ebay_price, potential_profit, profit_percentage))
            conn.commit()
    
    def get_all_products(self) -> List[Dict]:
        """Get all tracked products"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM products')
            return [dict(row) for row in cursor.fetchall()]
    
    def get_products_by_retailer(self, retailer: str) -> List[Dict]:
        """Get products from a specific retailer"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM products WHERE retailer = ?', (retailer,))
            return [dict(row) for row in cursor.fetchall()]
    
    def mark_deal_notified(self, deal_id: int):
        """Mark a deal as having been notified"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('UPDATE deals SET notified = TRUE WHERE id = ?', (deal_id,))
            conn.commit()
