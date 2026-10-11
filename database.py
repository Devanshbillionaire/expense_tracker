"""
database.py
------------
Handles all SQLite database operations for the Personal Expense Tracker.

This module defines the Database class, which is responsible for:
    - Creating the database file and required tables (with foreign keys)
    - Providing a single, reusable connection object
    - Exposing small helper methods used across the rest of the app

Tables:
    users     -> stores registered users and their hashed passwords
    income    -> income records linked to a user
    expenses  -> expense records linked to a user
    budget    -> monthly budget records linked to a user
"""

import os
import sqlite3
from sqlite3 import Connection
from typing import Optional


# Absolute path to the database directory / file so the app works
# regardless of the current working directory it is launched from.
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_DIR = os.path.join(BASE_DIR, "database")
DB_PATH = os.path.join(DB_DIR, "expense.db")


class Database:
    """A thin wrapper around a single SQLite connection.

    The class follows a simple singleton-like usage pattern: create one
    instance and share it across the application (see main.py) so that
    all modules read/write the same connection/cursor safely.
    """

    def __init__(self, db_path: str = DB_PATH) -> None:
        os.makedirs(DB_DIR, exist_ok=True)
        self.db_path = db_path
        self.conn: Connection = sqlite3.connect(self.db_path, check_same_thread=False)
        self.conn.execute("PRAGMA foreign_keys = ON;")
        self.conn.row_factory = sqlite3.Row
        self.cursor = self.conn.cursor()
        self._create_tables()

    # ------------------------------------------------------------------
    # Schema creation
    # ------------------------------------------------------------------
    def _create_tables(self) -> None:
        """Create all required tables if they do not already exist."""

        self.cursor.executescript(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                salt TEXT NOT NULL,
                created_at TEXT DEFAULT (datetime('now'))
            );

            CREATE TABLE IF NOT EXISTS income (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                amount REAL NOT NULL,
                source TEXT NOT NULL,
                date TEXT NOT NULL,
                notes TEXT,
                created_at TEXT DEFAULT (datetime('now')),
                FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS expenses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                amount REAL NOT NULL,
                category TEXT NOT NULL,
                date TEXT NOT NULL,
                payment_method TEXT,
                notes TEXT,
                created_at TEXT DEFAULT (datetime('now')),
                FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS budget (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                month INTEGER NOT NULL,
                year INTEGER NOT NULL,
                amount REAL NOT NULL,
                UNIQUE(user_id, month, year),
                FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS settings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL UNIQUE,
                theme TEXT DEFAULT 'light',
                currency TEXT DEFAULT 'INR',
                FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS deleted_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                item_type TEXT NOT NULL,
                item_data TEXT NOT NULL,
                deleted_at TEXT DEFAULT (datetime('now')),
                FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
            );
            """
        )
        self.conn.commit()

    # ------------------------------------------------------------------
    # Generic helpers
    # ------------------------------------------------------------------
    def execute(self, query: str, params: tuple = ()) -> sqlite3.Cursor:
        """Execute a write query (INSERT/UPDATE/DELETE) and commit."""
        cur = self.conn.execute(query, params)
        self.conn.commit()
        return cur

    def fetch_all(self, query: str, params: tuple = ()) -> list:
        """Execute a SELECT query and return all rows."""
        return self.conn.execute(query, params).fetchall()

    def fetch_one(self, query: str, params: tuple = ()) -> Optional[sqlite3.Row]:
        """Execute a SELECT query and return a single row (or None)."""
        return self.conn.execute(query, params).fetchone()

    def close(self) -> None:
        """Close the underlying connection."""
        self.conn.close()

    def backup(self, destination_path: str) -> None:
        """Create a full backup copy of the database file."""
        import shutil

        self.conn.commit()
        shutil.copyfile(self.db_path, destination_path)

    def restore(self, source_path: str) -> None:
        """Restore the database from a backup file, replacing current data."""
        import shutil

        self.close()
        shutil.copyfile(source_path, self.db_path)
        # Reconnect after restoring
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self.conn.execute("PRAGMA foreign_keys = ON;")
        self.conn.row_factory = sqlite3.Row
        self.cursor = self.conn.cursor()
