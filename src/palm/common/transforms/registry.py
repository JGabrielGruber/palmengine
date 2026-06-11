"""
Common transform registry — rich rules registered into the core engine.
"""

from __future__ import annotations

import threading
from typing import TYPE_CHECKING

from palm.core.registry import transform_registry

if TYPE_CHECKING:
    from palm.core.transform.base_transform import BaseTransform

_lock = threading.RLock()
_common_entries: dict[str, type[BaseTransform]] = {}


def register_common_transform(name: str, implementation: type[BaseTransform]) -> None:
    """
    Register a transform rule for common and pattern layers.

    Also wires the rule into :data:`~palm.core.registry.transform_registry` so
    :class:`~palm.core.transform.engine.TransformEngine` can resolve it by name.
    """
    with _lock:
        if _common_entries.get(name) is implementation:
            return
        _common_entries[name] = implementation
        transform_registry.register(name, implementation)


def registered_common_transforms() -> list[str]:
    with _lock:
        return sorted(_common_entries)


def clear_common_transforms() -> None:
    """Remove common registrations (primarily for tests)."""
    with _lock:
        _common_entries.clear()