"""
Utility functions for reporting module.

Common utilities shared across reporting components.
"""

from datetime import datetime
from typing import Any


def parse_timestamp(timestamp: Any) -> datetime | None:
    """
    Parse a timestamp from various formats.

    Args:
        timestamp: Timestamp as string, datetime, or other

    Returns:
        datetime object or None if parsing fails
    """
    if isinstance(timestamp, str):
        try:
            return datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
        except (ValueError, AttributeError):
            return None
    elif isinstance(timestamp, datetime):
        return timestamp
    return None
