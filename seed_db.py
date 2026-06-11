"""
seed_db.py - Creates and populates the ecommerce.db SQLite database with mock data.
Uses a fixed random seed for reproducibility.
"""

import sqlite3
import random
from datetime import datetime, timedelta
from faker import Faker

# Fixed seed for reproducibility
Faker.seed(42)
random.seed(42)
fake = Faker()

DB_PATH = "ecommerce.db"

CATEGORIES = ["Electronics", "Clothing", "Books", "Home & Kitchen", "Sports", "Beauty", "Toys", "Automotive"]

PRODUCTS_DATA = [
    ("Wireless Bluetooth Headphones", "Electronics", 79.99, 150),
    ("Running Shoes Pro", "Sports", 129.99, 80),
    ("Stainless Steel Water Bottle", "Sports", 24.99, 200),
    ("Python Programming Book", "Books", 39.99, 60),
    ("Smart LED Desk Lamp", "Electronics", 49.99, 0),
    ("Yoga Mat Premium", "Sports", 34.99, 120),
    ("Coffee Maker Deluxe", "Home & Kitchen", 89.99, 45),
    ("Winter Puffer Jacket", "Clothing", 149.99, 30),
    ("Mechanical Keyboard RGB", "Electronics", 119.99, 0),
    ("Moisturizing Face Cream", "Beauty", 29.99, 90),
    ("Action Figure Set", "Toys", 19.99, 75),
    ("Car Phone Mount", "Automotive", 14.99, 110),
    ("Dumbbell Set 20kg", "Sports", 59.99, 25),
    ("Non-Stick Frying Pan", "Home & Kitchen", 44.99, 55),
    ("Classic Novel Collection", "Books", 34.99, 40),
    ("Portable Charger 20000mAh", "Electronics", 39.99, 85),
    ("Slim Fit Chinos", "Clothing", 54.99, 0),
    ("Aromatherapy Diffuser", "Home & Kitchen", 27.99, 65),
    ("Sunscreen SPF50", "Beauty", 16.99, 130),
    ("Remote Control Car", "Toys", 44.99, 50),
    ("Dashcam HD 1080p", "Automotive", 69.99, 35),
    ("Resistance Bands Set", "Sports", 18.99, 95),
    ("Air Fryer 5L", "Home & Kitchen", 99.99, 0),
    ("Graphic T-Shirt Pack", "Clothing", 29.99, 200),
    ("Machine Learning Book", "Books", 49.99, 45),
    ("Wireless Mouse", "Electronics", 34.99, 110),
    ("Hiking Boots", "Sports", 109.99, 40),
    ("Shampoo & Conditioner Set", "Beauty", 22.99, 80),
    ("Building Blocks 500pc", "Toys", 34.99, 60),
    ("Leather Wallet", "Clothing", 39.99, 0),
]

ORDER_STATUSES = ["processing", "shipped", "delivered", "cancelled"]
RETURN_STATUSES = ["pending", "approved", "rejected", "completed"]


def create_tables(conn):
    cursor = conn.cursor()
    cursor.executescript("""
        DROP TABLE IF EXISTS returns;
        DROP TABLE IF EXISTS orders;
        DROP TABLE IF EXISTS products;
        DROP TABLE IF EXISTS customers;

        CREATE TABLE customers (
            customer_id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            phone TEXT,
            address TEXT,
            city TEXT,
            state TEXT,
            zip_code TEXT,
            created_at TEXT NOT NULL
        );

        CREATE TABLE products (
            product_id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            category TEXT NOT NULL,
            price REAL NOT NULL,
            stock_count INTEGER NOT NULL DEFAULT 0,
            rating REAL DEFAULT 4.0,
            description TEXT,
            created_at TEXT NOT NULL
        );

        CREATE TABLE orders (
            order_id TEXT PRIMARY KEY,
            customer_id TEXT NOT NULL,
            product_id TEXT NOT NULL,
            quantity INTEGER NOT NULL DEFAULT 1,
            total_price REAL NOT NULL,
            status TEXT NOT NULL CHECK(status IN ('processing', 'shipped', 'delivered', 'cancelled')),
            tracking_number TEXT,
            estimated_delivery TEXT,
            actual_delivery TEXT,
            created_at TEXT NOT NULL,
            FOREIGN KEY (customer_id) REFERENCES customers(customer_id),
            FOREIGN KEY (product_id) REFERENCES products(product_id)
        );

        CREATE TABLE returns (
            return_id TEXT PRIMARY KEY,
            order_id TEXT NOT NULL,
            customer_id TEXT NOT NULL,
            reason TEXT NOT NULL,
            status TEXT NOT NULL CHECK(status IN ('pending', 'approved', 'rejected', 'completed')),
            refund_amount REAL,
            initiated_at TEXT NOT NULL,
            resolved_at TEXT,
            FOREIGN KEY (order_id) REFERENCES orders(order_id),
            FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
        );
    """)
    conn.commit()
    print("✓ Tables created successfully.")



def main():
    print('Tables initialized')
if __name__ == '__main__':
    main()