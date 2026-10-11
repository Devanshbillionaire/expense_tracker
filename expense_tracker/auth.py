"""
auth.py
-------
Handles user authentication: registration, login and password hashing.

Passwords are never stored in plain text. We use PBKDF2-HMAC (SHA-256)
with a unique random salt per user, which is a strong, dependency-free
way to hash passwords using only the Python standard library.
"""

import hashlib
import os
import re
from dataclasses import dataclass
from typing import Optional

from database import Database


PBKDF2_ITERATIONS = 200_000


@dataclass
class User:
    """Simple data holder representing a logged-in user."""
    id: int
    username: str


class AuthError(Exception):
    """Raised for any authentication-related failure (bad input, etc.)."""


class AuthManager:
    """Provides register/login/logout functionality backed by SQLite."""

    def __init__(self, db: Database) -> None:
        self.db = db

    # ------------------------------------------------------------------
    # Password hashing helpers
    # ------------------------------------------------------------------
    @staticmethod
    def _hash_password(password: str, salt: Optional[bytes] = None) -> tuple[str, str]:
        """Return (hash_hex, salt_hex) for the given password."""
        if salt is None:
            salt = os.urandom(16)
        pwd_hash = hashlib.pbkdf2_hmac(
            "sha256", password.encode("utf-8"), salt, PBKDF2_ITERATIONS
        )
        return pwd_hash.hex(), salt.hex()

    @staticmethod
    def _verify_password(password: str, stored_hash: str, stored_salt: str) -> bool:
        salt = bytes.fromhex(stored_salt)
        pwd_hash = hashlib.pbkdf2_hmac(
            "sha256", password.encode("utf-8"), salt, PBKDF2_ITERATIONS
        )
        return pwd_hash.hex() == stored_hash

    # ------------------------------------------------------------------
    # Validation
    # ------------------------------------------------------------------
    @staticmethod
    def _validate_username(username: str) -> None:
        if not username or not username.strip():
            raise AuthError("Username cannot be empty.")
        if len(username) < 3:
            raise AuthError("Username must be at least 3 characters long.")
        if not re.match(r"^[A-Za-z0-9_.]+$", username):
            raise AuthError(
                "Username may only contain letters, numbers, underscores and dots."
            )

    @staticmethod
    def _validate_password(password: str) -> None:
        if not password:
            raise AuthError("Password cannot be empty.")
        if len(password) < 6:
            raise AuthError("Password must be at least 6 characters long.")

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def register(self, username: str, password: str, confirm_password: str) -> User:
        """Register a new user. Raises AuthError on any validation failure."""
        username = username.strip()
        self._validate_username(username)
        self._validate_password(password)

        if password != confirm_password:
            raise AuthError("Passwords do not match.")

        existing = self.db.fetch_one(
            "SELECT id FROM users WHERE username = ?", (username,)
        )
        if existing is not None:
            raise AuthError(f"Username '{username}' is already taken.")

        pwd_hash, salt = self._hash_password(password)
        cur = self.db.execute(
            "INSERT INTO users (username, password_hash, salt) VALUES (?, ?, ?)",
            (username, pwd_hash, salt),
        )
        user_id = cur.lastrowid
        # Create default settings row for the new user
        self.db.execute(
            "INSERT INTO settings (user_id, theme, currency) VALUES (?, 'light', 'INR')",
            (user_id,),
        )
        return User(id=user_id, username=username)

    def login(self, username: str, password: str) -> User:
        """Authenticate a user. Raises AuthError if credentials are invalid."""
        username = username.strip()
        if not username or not password:
            raise AuthError("Please enter both username and password.")

        row = self.db.fetch_one(
            "SELECT id, username, password_hash, salt FROM users WHERE username = ?",
            (username,),
        )
        if row is None:
            raise AuthError("Invalid username or password.")

        if not self._verify_password(password, row["password_hash"], row["salt"]):
            raise AuthError("Invalid username or password.")

        return User(id=row["id"], username=row["username"])
