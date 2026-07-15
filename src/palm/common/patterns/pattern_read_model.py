"""
Pattern read-model dispatch — registry-backed REST view assembly.
"""

from __future__ import annotations

from typing import Any

from palm.common.patterns._registry import get_read_model_builder


def build_pattern_read_model(
    pattern: str,
    instance: dict[str, Any],
    /,
    **kwargs: Any,
) -> dict[str, Any]:
    """Dispatch a registered pattern read-model builder."""

    builder = get_read_model_builder(pattern)
    if builder is None:
        raise RuntimeError(f"No read-model builder registered for pattern {pattern!r}")
    return builder(instance, **kwargs)


__all__ = ["build_pattern_read_model"]
