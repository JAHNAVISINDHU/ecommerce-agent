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