"""
DAG pattern builder — parse FlowDefinition.options into DagConfig (0.54.3).
"""

from __future__ import annotations

from palm.common.exceptions import DefinitionBuildError
from palm.common.patterns.build_context import PatternBuildContext
from palm.common.patterns.effects import resolve_resource_invoker, resolve_workload_driver
from palm.core.behavior_tree import BasePattern
from palm.definitions.flow import FlowDefinition
from plugins.patterns.dag.bindings.definitions.config import DagConfig


def build(
    flow: FlowDefinition,
    context: PatternBuildContext,
    pattern_cls: type[BasePattern],
) -> BasePattern:
    """Instantiate a DAG pattern from a flow definition."""
    options = dict(flow.options or {})
    # name is optional cosmetic
    options.pop("name", None)
    try:
        config = DagConfig.from_options(options)
    except ValueError as exc:
        raise DefinitionBuildError(str(exc)) from exc
    return pattern_cls(
        name=str(flow.options.get("name") or flow.name),
        config=config,
        resource_engine=resolve_resource_invoker(context),
        workload_engine=resolve_workload_driver(context),
    )


__all__ = ["build"]
