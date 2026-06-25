"""
ETL pattern builder — parse ``FlowDefinition.options`` for etl flows.
"""

from __future__ import annotations

from palm.common.exceptions import DefinitionBuildError
from palm.common.patterns.build_context import PatternBuildContext
from palm.core.behavior_tree import BasePattern
from palm.definitions.flow import FlowDefinition


def build(
    flow: FlowDefinition,
    context: PatternBuildContext,
    pattern_cls: type[BasePattern],
) -> BasePattern:
    """Instantiate an ETL pattern from a flow definition."""
    del context
    allowed = {"name"}
    unknown = set(flow.options) - allowed
    if unknown:
        raise DefinitionBuildError(
            f"Pattern {flow.pattern!r} does not support options: {sorted(unknown)}"
        )
    return pattern_cls(name=flow.options.get("name", flow.name))
