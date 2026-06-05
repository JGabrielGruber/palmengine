"""
Time utilities with UTC-only semantics.

All timestamps in Palm are timezone-aware UTC.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta


def utc_now() -> datetime:
    """Return current UTC datetime (timezone-aware)."""
    return datetime.now(UTC)


def add_seconds(dt: datetime, seconds: int | float) -> datetime:
    """Add seconds to a datetime, preserving timezone awareness."""
    if dt.tzinfo is None:
        # Assume UTC if naive (defensive)
        dt = dt.replace(tzinfo=UTC)
    return dt + timedelta(seconds=seconds)


def is_expired(expires_at: datetime | None, now: datetime | None = None) -> bool:
    """Return True if expires_at is in the past."""
    if expires_at is None:
        return False
    now = now or utc_now()
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=UTC)
    return now >= expires_at
