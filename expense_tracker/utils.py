"""
utils.py
--------
Shared, dependency-light helper functions used across multiple modules:
    - input validation (amount, date)
    - currency formatting
    - category / payment-method constants

Keeping these in one place avoids duplicating validation logic in
income.py, expense.py and budget.py.
"""

from datetime import datetime
from typing import Optional


class ValidationError(Exception):
    """Raised when user input fails validation."""


EXPENSE_CATEGORIES = [
    "Food",
    "Transport",
    "Shopping",
    "Entertainment",
    "Education",
    "Medical",
    "Rent",
    "Bills",
    "Travel",
    "Others",
]

PAYMENT_METHODS = ["Cash", "Credit Card", "Debit Card", "UPI", "Net Banking", "Other"]

CURRENCIES = {
    "INR": "\u20b9",
    "USD": "$",
    "EUR": "\u20ac",
    "GBP": "\u00a3",
}

DATE_FORMAT = "%Y-%m-%d"


def validate_amount(value: str) -> float:
    """Validate that value is a positive, numeric amount. Returns the float."""
    if value is None or str(value).strip() == "":
        raise ValidationError("Amount cannot be empty.")
    try:
        amount = float(value)
    except ValueError:
        raise ValidationError("Amount must be a valid number.")
    if amount <= 0:
        raise ValidationError("Amount must be greater than zero.")
    return round(amount, 2)


def validate_date(value: str) -> str:
    """Validate a date string in YYYY-MM-DD format. Returns the normalized string."""
    if not value or not value.strip():
        raise ValidationError("Date cannot be empty.")
    try:
        parsed = datetime.strptime(value.strip(), DATE_FORMAT)
    except ValueError:
        raise ValidationError("Date must be in YYYY-MM-DD format, e.g. 2026-08-05.")
    return parsed.strftime(DATE_FORMAT)


def validate_not_empty(value: str, field_name: str) -> str:
    """Validate that a text field is not empty/whitespace."""
    if value is None or not str(value).strip():
        raise ValidationError(f"{field_name} cannot be empty.")
    return str(value).strip()


def format_currency(amount: float, symbol: str = "\u20b9") -> str:
    """Format a numeric amount as a currency string, e.g. Rs. 1,234.50"""
    try:
        return f"{symbol}{amount:,.2f}"
    except (TypeError, ValueError):
        return f"{symbol}0.00"


def current_month_year() -> tuple[int, int]:
    now = datetime.now()
    return now.month, now.year
