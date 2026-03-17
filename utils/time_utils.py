"""Timestamp normalization — parse various formats and return UTC ISO strings."""

import re
from datetime import datetime, timezone
from typing import Optional

# Common formats from RSS, News API, OpenWeather, etc.
_FORMATS = [
    "%Y-%m-%dT%H:%M:%S.%fZ",
    "%Y-%m-%dT%H:%M:%SZ",
    "%Y-%m-%dT%H:%M:%S%z",
    "%Y-%m-%dT%H:%M:%S.%f%z",
    "%Y-%m-%d %H:%M:%S",
    "%Y-%m-%d %H:%M:%S.%f",
    "%a, %d %b %Y %H:%M:%S %Z",
    "%a, %d %b %Y %H:%M:%S %z",
    "%a, %d %b %Y %H:%M:%S",
    "%d %b %Y %H:%M:%S %Z",
    "%Y-%m-%d",
    "%d/%m/%Y %H:%M:%S",
    "%m/%d/%Y %H:%M:%S",
]

# RFC 2822 with timezone names (e.g. "GMT", "EST")
_RFC2822_TZ = re.compile(r"([+-]\d{4}|GMT|EST|PST|CST|MST|EDT|PDT|CDT|MDT)\s*$", re.I)


def normalize_timestamp(value) -> str:
    """Convert any timestamp to UTC ISO 8601 string.

    Accepts: datetime, int (unix), float, or str in common formats.
    Returns: "YYYY-MM-DDTHH:MM:SS.ffffff+00:00"
    """
    if value is None or value == "":
        return datetime.now(timezone.utc).isoformat()

    if isinstance(value, datetime):
        if value.tzinfo is None:
            value = value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc).isoformat()

    if isinstance(value, (int, float)):
        try:
            dt = datetime.fromtimestamp(value, tz=timezone.utc)
            return dt.isoformat()
        except (ValueError, OSError):
            return datetime.now(timezone.utc).isoformat()

    if isinstance(value, str):
        value = value.strip()
        if not value:
            return datetime.now(timezone.utc).isoformat()

        # Try parsing as unix timestamp
        try:
            return normalize_timestamp(float(value))
        except ValueError:
            pass

        for fmt in _FORMATS:
            try:
                dt = datetime.strptime(value, fmt)
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=timezone.utc)
                return dt.astimezone(timezone.utc).isoformat()
            except ValueError:
                continue

        # Feedparser-style: "Mon, 01 Jan 2024 12:00:00 GMT"
        if _RFC2822_TZ.search(value):
            try:
                from email.utils import parsedate_to_datetime
                dt = parsedate_to_datetime(value)
                return dt.astimezone(timezone.utc).isoformat()
            except Exception:
                pass

    return datetime.now(timezone.utc).isoformat()
