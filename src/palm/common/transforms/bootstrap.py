"""
Bootstrap common transform rules into the core registry.
"""

from __future__ import annotations

import threading

from palm.common.transforms.registry import register_common_transform
from palm.common.transforms.rules import (
    CalculateTransform,
    DropFieldsTransform,
    FilterListTransform,
    FormatDateTransform,
    FormatStringTransform,
    LowercaseTransform,
    MapListTransform,
    PickFieldsTransform,
    RenameTransform,
    UppercaseTransform,
)

_lock = threading.RLock()
_bootstrapped = False

_COMMON_RULES: tuple[type, ...] = (
    RenameTransform,
    PickFieldsTransform,
    DropFieldsTransform,
    FormatStringTransform,
    FormatDateTransform,
    UppercaseTransform,
    LowercaseTransform,
    FilterListTransform,
    MapListTransform,
    CalculateTransform,
)


def register_common_transforms() -> None:
    """Register all built-in common transforms (idempotent)."""
    global _bootstrapped
    with _lock:
        for cls in _COMMON_RULES:
            register_common_transform(cls.name, cls)
        _bootstrapped = True


def ensure_common_transforms() -> None:
    """Register common transforms once per process."""
    if not _bootstrapped:
        register_common_transforms()