"""Shared helpers for serialization transform rules."""

from __future__ import annotations

from typing import Any

from palm.core.exceptions import TransformApplicationError


def ensure_text(value: Any, *, encoding: str, rule_name: str) -> str:
    """Return ``value`` as text, decoding bytes when needed."""
    if isinstance(value, str):
        return value
    if isinstance(value, bytes):
        try:
            return value.decode(encoding)
        except UnicodeDecodeError as exc:
            raise TransformApplicationError(
                f"{rule_name} could not decode bytes with encoding {encoding!r}",
            ) from exc
    raise TransformApplicationError(
        f"{rule_name} requires str or bytes, got {type(value).__name__}",
    )


def optional_text_or_bytes(value: Any, *, encoding: str, rule_name: str) -> str | bytes:
    """Accept str or bytes payloads for format loaders."""
    if isinstance(value, (str, bytes)):
        return value
    raise TransformApplicationError(
        f"{rule_name} requires str or bytes, got {type(value).__name__}",
    )