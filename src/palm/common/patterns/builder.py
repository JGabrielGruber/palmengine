"""
Definition builder — resolves ``FlowDefinition`` into concrete patterns.

Dispatches to per-pattern builders registered in ``palm.patterns.<app>.builder``.
"""

from __future__ import annotations

import palm.patterns  # noqa: F401 — autoload installed pattern apps
from palm.common.exceptions import DefinitionBuildError
from palm.common.patterns.build_context import PatternBuildContext
from palm.core.behavior_tree import BasePattern
from palm.core.event import EventEngine
from palm.core.registry import pattern_registry
from palm.definitions.flow import FlowDefinition
from palm.patterns._registry import get_builder

__all__ = ["build_pattern"]


def build_pattern(
    flow: FlowDefinition,
    *,
    event_engine: EventEngine | None = None,
    context: PatternBuildContext | None = None,
) -> BasePattern:
    """
    Instantiate a registered pattern from a flow definition.

    Pattern-specific option parsing lives in each pattern app; this function
    only resolves the registry entry and delegates to the app's builder.
    """
    try:
        pattern_cls = pattern_registry.get(flow.pattern)
    except Exception as exc:
        raise DefinitionBuildError(
            f"Cannot resolve pattern {flow.pattern!r} for flow {flow.name!r}"
        ) from exc

    ctx = context or PatternBuildContext(event_engine=event_engine)
    if event_engine is not None and ctx.event_engine is None:
        ctx.event_engine = event_engine

    builder = get_builder(flow.pattern)
    if builder is not None:
        return builder(flow, ctx, pattern_cls)

    if flow.options:
        raise DefinitionBuildError(f"Pattern {flow.pattern!r} does not support flow options yet")

    return pattern_cls(name=flow.name)
