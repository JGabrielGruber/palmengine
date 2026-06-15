"""Shared date parsing and formatting helpers for transform rules."""

from __future__ import annotations

from datetime import date, datetime
from typing import Any

from palm.core.exceptions import TransformApplicationError


def parse_datetime_value(value: Any, *, input_format: str | None = None) -> datetime:
    """Parse a date, datetime, or string into a timezone-naive datetime."""
    if isinstance(value, datetime):
        return value
    if isinstance(value, date):
        return datetime(value.year, value.month, value.day)
    if isinstance(value, str):
        if input_format:
            try:
                return datetime.strptime(value, input_format)
            except ValueError as exc:
                raise TransformApplicationError(
                    f"date_parse could not parse {value!r} with format {input_format!r}",
                ) from exc
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00")).replace(tzinfo=None)
        except ValueError as exc:
            raise TransformApplicationError(
                f"date_parse could not parse ISO string {value!r}",
            ) from exc
    raise TransformApplicationError(
        f"expected date, datetime, or string, got {type(value).__name__}",
    )


def format_datetime_value(value: Any, fmt: str, *, input_format: str | None = None) -> str:
    """Format a date-like value with ``strftime``."""
    if not fmt:
        raise TransformApplicationError("date_format requires a format string")
    parsed = parse_datetime_value(value, input_format=input_format)
    return parsed.strftime(fmt)