"""Human-readable value previews for CLI and wizard transform feedback."""

from __future__ import annotations

from typing import Any


def preview_value(value: Any, *, max_len: int = 72) -> str:
    """Return a compact, operator-facing preview of ``value``."""
    if value is None:
        return "∅"
    if isinstance(value, str):
        text = value
    elif isinstance(value, (int, float, bool)):
        text = repr(value)
    else:
        text = repr(value)
    if len(text) <= max_len:
        return text
    return f"{text[: max_len - 1]}…"