"""Formatting utilities for dates, currency, and other display values."""

from datetime import date
from decimal import Decimal
from typing import Optional


def format_date(value: Optional[date]) -> str:
    """
    Format date as MM/DD/YYYY or return N/A if None.

    Args:
        value: Date to format

    Returns:
        Formatted date string or "N/A"
    """
    if value is None:
        return "N/A"
    return value.strftime("%m/%d/%Y")


def format_currency(amount: Optional[Decimal], currency_id: str = "USD") -> str:
    """
    Format decimal amount as currency with $ symbol and thousand separators.

    Args:
        amount: Decimal amount to format
        currency_id: Currency identifier (default: USD)

    Returns:
        Formatted currency string or "N/A"
    """
    if amount is None:
        return "N/A"

    # Currently only USD supported
    if currency_id == "USD":
        return f"${amount:,.2f}"
    else:
        # Fallback for other currencies
        return f"{currency_id} {amount:,.2f}"


def format_nullable_string(value: Optional[str], default: str = "N/A") -> str:
    """
    Format optional string, returning default if None or empty.

    Args:
        value: String value to format
        default: Default value if None or empty (default: "N/A")

    Returns:
        Value or default string
    """
    if value is None or value.strip() == "":
        return default
    return value.strip()


def format_phone(value: Optional[str]) -> str:
    """
    Format phone number or return N/A if None.

    Args:
        value: Phone number string

    Returns:
        Formatted phone or "N/A"
    """
    if value is None or value.strip() == "":
        return "N/A"

    # Basic formatting - remove non-numeric characters and format
    digits = "".join(c for c in value if c.isdigit())

    if len(digits) == 10:
        return f"({digits[:3]}) {digits[3:6]}-{digits[6:]}"
    elif len(digits) == 11 and digits[0] == "1":
        return f"+1 ({digits[1:4]}) {digits[4:7]}-{digits[7:]}"
    else:
        # Return as-is if doesn't match expected format
        return value.strip()


def format_quantity(value: Decimal, max_decimals: int = 4) -> str:
    """
    Format quantity with up to max_decimals decimal places, removing trailing zeros.

    Args:
        value: Decimal quantity value
        max_decimals: Maximum decimal places to show (default: 4)

    Returns:
        Formatted quantity string
    """
    format_str = f"{{:.{max_decimals}f}}"
    formatted = format_str.format(value)
    # Remove trailing zeros and decimal point if not needed
    return formatted.rstrip("0").rstrip(".")
