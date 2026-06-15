"""Shared validation helpers for common transform rules."""

from __future__ import annotations

from typing import Any

from palm.core.exceptions import TransformApplicationError


def require_mapping(value: Any, rule_name: str) -> dict[str, Any]:
    """Return ``value`` when it is a mapping; raise otherwise."""
    if not isinstance(value, dict):
        raise TransformApplicationError(
            f"{rule_name} requires a mapping, got {type(value).__name__}",
        )
    return value


def require_list(value: Any, rule_name: str) -> list[Any]:
    """Return ``value`` when it is a list; raise otherwise."""
    if not isinstance(value, list):
        raise TransformApplicationError(
            f"{rule_name} requires a list, got {type(value).__name__}",
        )
    return value
