"""
tools/db_tools.py - Database query tools for sub-agents.
"""

import sqlite3
import os
from typing import Any, Dict, List, Optional
from langchain_core.tools import tool

DB_PATH = os.environ.get("DB_PATH", "ecommerce.db")


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def rows_to_dicts(rows) -> List[Dict]:
    return [dict(row) for row in rows]


# ─── Order Tools ────────────────────────────────────────────────────────────

@tool
def get_orders_by_customer(customer_id: str) -> List[Dict]:
    """Retrieve all orders for a given customer ID."""
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT o.order_id, o.status, o.tracking_number, o.estimated_delivery,
                   o.actual_delivery, o.total_price, o.created_at, o.quantity,
                   p.name as product_name, p.category
            FROM orders o
            JOIN products p ON o.product_id = p.product_id
            WHERE o.customer_id = ?
            ORDER BY o.created_at DESC
        """, (customer_id,))
        return rows_to_dicts(cursor.fetchall())
    finally:
        conn.close()


@tool
def get_order_by_id(order_id: str) -> Optional[Dict]:
    """Retrieve a specific order by its order ID."""
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT o.order_id, o.customer_id, o.status, o.tracking_number,
                   o.estimated_delivery, o.actual_delivery, o.total_price,
                   o.created_at, o.quantity,
                   p.name as product_name, p.category, p.product_id
            FROM orders o
            JOIN products p ON o.product_id = p.product_id
            WHERE o.order_id = ?
        """, (order_id,))
        row = cursor.fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


@tool
def get_active_orders_by_customer(customer_id: str) -> List[Dict]:
    """Get active (non-cancelled, non-delivered) orders for a customer."""
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT o.order_id, o.status, o.tracking_number, o.estimated_delivery,
                   o.total_price, o.created_at, o.quantity,
                   p.name as product_name, p.category
            FROM orders o
            JOIN products p ON o.product_id = p.product_id
            WHERE o.customer_id = ? AND o.status IN ('processing', 'shipped')
            ORDER BY o.created_at DESC
        """, (customer_id,))
        return rows_to_dicts(cursor.fetchall())
    finally:
        conn.close()


# ─── Product Tools ───────────────────────────────────────────────────────────

@tool
def search_products(query: str) -> List[Dict]:
    """Search for products by name or category (case-insensitive partial match)."""
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT product_id, name, category, price, stock_count, rating, description
            FROM products
            WHERE LOWER(name) LIKE ? OR LOWER(category) LIKE ?
            ORDER BY rating DESC
            LIMIT 5
        """, (f"%{query.lower()}%", f"%{query.lower()}%"))
        return rows_to_dicts(cursor.fetchall())
    finally:
        conn.close()


@tool
def get_product_by_id(product_id: str) -> Optional[Dict]:
    """Get a product by its exact product ID."""
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM products WHERE product_id = ?", (product_id,)
        )
        row = cursor.fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


@tool
def get_products_by_category(category: str, max_price: Optional[float] = None) -> List[Dict]:
    """Get products by category, optionally filtered by max price, sorted by rating."""
    conn = get_connection()
    try:
        cursor = conn.cursor()
        if max_price:
            cursor.execute("""
                SELECT product_id, name, category, price, stock_count, rating
                FROM products
                WHERE LOWER(category) LIKE ? AND price <= ?
                ORDER BY rating DESC LIMIT 5
            """, (f"%{category.lower()}%", max_price))
        else:
            cursor.execute("""
                SELECT product_id, name, category, price, stock_count, rating
                FROM products
                WHERE LOWER(category) LIKE ?
                ORDER BY rating DESC LIMIT 5
            """, (f"%{category.lower()}%",))
        return rows_to_dicts(cursor.fetchall())
    finally:
        conn.close()


@tool
def get_top_rated_products(max_price: Optional[float] = None, limit: int = 5) -> List[Dict]:
    """Get top-rated products from the entire catalog, optionally filtered by price."""
    conn = get_connection()
    try:
        cursor = conn.cursor()
        if max_price:
            cursor.execute("""
                SELECT product_id, name, category, price, stock_count, rating
                FROM products WHERE stock_count > 0 AND price <= ?
                ORDER BY rating DESC LIMIT ?
            """, (max_price, limit))
        else:
            cursor.execute("""
                SELECT product_id, name, category, price, stock_count, rating
                FROM products WHERE stock_count > 0
                ORDER BY rating DESC LIMIT ?
            """, (limit,))
        return rows_to_dicts(cursor.fetchall())
    finally:
        conn.close()

