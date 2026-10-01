"""
Definition builder — resolves ``FlowDefinition`` into concrete patterns.

Dispatches to per-pattern builders registered in ``palm.patterns.<app>.builder``.
"""

from __future__ import annotations

from typing import cast

from palm.common.exceptions import DefinitionBuildError
from palm.common.patterns.build_context import PatternBuildContext
from palm.core.behavior_tree import BasePattern
from palm.core.event import EventEngine
from palm.definitions.flow import FlowDefinition

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
    resolves the pattern from the system registries on ``context``.
    """
    if context is None or context.registries is None:
        raise DefinitionBuildError(
            f"pattern build has no system registries for flow {flow.name!r}"
        )
    registries = context.registries
    try:
        pattern_cls = registries.require("pattern").get(flow.pattern)
    except Exception as exc:
        raise DefinitionBuildError(
            f"Cannot resolve pattern {flow.pattern!r} for flow {flow.name!r}"
        ) from exc

    if event_engine is not None and context.event_engine is None:
        context.event_engine = event_engine

    builder = None
    if "pattern_builder" in registries.names():
        builders = registries.require("pattern_builder")
        if flow.pattern in builders.names():
            builder = builders.get(flow.pattern)
    if builder is not None:
        return cast(BasePattern, builder(flow, context, pattern_cls))

    if flow.options:
        raise DefinitionBuildError(f"Pattern {flow.pattern!r} does not support flow options yet")

    return cast(BasePattern, pattern_cls(name=flow.name))
