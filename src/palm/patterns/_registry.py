"""
Pattern builder registry — each pattern app registers its own build logic.

Keeps ``palm.common.patterns.builder`` generic; pattern-specific option parsing
lives inside the owning ``palm.patterns.<name>`` subpackage.
"""

from __future__ import annotations

import threading
from collections.abc import Callable
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from palm.common.patterns.build_context import PatternBuildContext
    from palm.core.behavior_tree import BasePattern
    from palm.definitions.flow import FlowDefinition

    PatternBuildFn = Callable[
        [FlowDefinition, PatternBuildContext, type[BasePattern]],
        BasePattern,
    ]
else:
    PatternBuildFn = Callable[..., Any]

_lock = threading.RLock()
_builders: dict[str, PatternBuildFn] = {}


def register_builder(name: str, fn: PatternBuildFn) -> None:
    """Register a flow-options builder for pattern ``name``."""
    with _lock:
        if _builders.get(name) is fn:
            return
        _builders[name] = fn


def get_builder(name: str) -> PatternBuildFn | None:
    """Return the registered builder for ``name``, if any."""
    with _lock:
        return _builders.get(name)


def registered_builders() -> list[str]:
    """Return sorted names of patterns with custom builders."""
    with _lock:
        return sorted(_builders)


def clear_builders() -> None:
    """Remove all builder registrations (primarily for tests)."""
    with _lock:
        _builders.clear()


def snapshot_builders() -> dict[str, PatternBuildFn]:
    """Return a shallow copy of registered builders (primarily for tests)."""
    with _lock:
        return dict(_builders)


def restore_builders(saved: dict[str, PatternBuildFn]) -> None:
    """Replace all builder registrations from a prior :func:`snapshot_builders` copy."""
    with _lock:
        _builders.clear()
        _builders.update(saved)