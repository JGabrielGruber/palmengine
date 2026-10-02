"""
Pattern read-model dispatch.

The caller passes the read-model builder table. A missing pattern name raises.
This module does not read the process table.
"""

from __future__ import annotations

from typing import Any

from palm.common.patterns._registry import ReadModelBuilderFn
from palm.core.registry import Registry


def build_pattern_read_model(
    pattern: str,
    instance: dict[str, Any],
    /,
    *,
    builders: Registry[ReadModelBuilderFn],
    **kwargs: Any,
) -> dict[str, Any]:
    """Build the view for ``pattern`` from ``builders``. A missing name raises."""

    return builders.get(pattern)(instance, **kwargs)


__all__ = ["build_pattern_read_model"]
