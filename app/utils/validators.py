"""
Input validation utilities
"""

import re
from typing import Literal


def validate_email(email: str) -> bool:
    """
    Validate email format

    Args:
        email: Email address to validate

    Returns:
        True if valid, False otherwise
    """
    pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    return re.match(pattern, email) is not None


def validate_password(password: str) -> tuple[bool, str]:
    """
    Validate password strength

    Args:
        password: Password to validate

    Returns:
        Tuple of (is_valid, error_message)
    """
    if len(password) < 6:
        return False, "Password must be at least 6 characters"
    return True, ""


def validate_category(
    category: str,
) -> tuple[bool, str]:
    """
    Validate category value

    Args:
        category: Category to validate

    Returns:
        Tuple of (is_valid, error_message)
    """
    valid_categories = ["ABOVE_AVERAGE", "AVERAGE", "GOOD", "POOR"]
    if category.upper() not in valid_categories:
        return (
            False,
            f"Invalid category. Must be one of: {', '.join(valid_categories)}",
        )
    return True, ""


def validate_name(name: str) -> tuple[bool, str]:
    """
    Validate name

    Args:
        name: Name to validate

    Returns:
        Tuple of (is_valid, error_message)
    """
    if not name or len(name) == 0:
        return False, "Name cannot be empty"
    if len(name) > 100:
        return False, "Name must be less than 100 characters"
    return True, ""


def validate_batch(batch: str) -> tuple[bool, str]:
    """
    Validate batch

    Args:
        batch: Batch to validate

    Returns:
        Tuple of (is_valid, error_message)
    """
    if not batch or len(batch) == 0:
        return False, "Batch cannot be empty"
    if len(batch) > 100:
        return False, "Batch must be less than 100 characters"
    return True, ""
