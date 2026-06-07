"""
Pattern builder registry — each pattern app registers its own build logic.

Keeps ``palm.common.patterns.builder`` generic; pattern-specific option parsing
lives inside the owning ``palm.patterns.<name>`` subpackage.
"""

from __future__ import annotations

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

_builders: dict[str, PatternBuildFn] = {}


def register_builder(name: str, fn: PatternBuildFn) -> None:
    """Register a flow-options builder for pattern ``name``."""
    _builders[name] = fn


def get_builder(name: str) -> PatternBuildFn | None:
    """Return the registered builder for ``name``, if any."""
    return _builders.get(name)


def registered_builders() -> list[str]:
    """Return sorted names of patterns with custom builders."""
    return sorted(_builders)