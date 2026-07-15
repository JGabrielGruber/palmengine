"""
Pipeline pattern builder — parse flow options into ``PipelinePattern`` instances.
"""

from __future__ import annotations

from palm.common.exceptions import DefinitionBuildError
from palm.common.patterns.build_context import PatternBuildContext
from palm.core.behavior_tree import BasePattern
from palm.definitions.flow import FlowDefinition
from palm.patterns.pipeline.bindings.definitions.config import PipelineConfig
from palm.patterns.pipeline.pattern import PipelinePattern


def build(
    flow: FlowDefinition,
    context: PatternBuildContext,
    pattern_cls: type[BasePattern],
) -> BasePattern:
    """Instantiate a pipeline pattern from a flow definition."""
    if not issubclass(pattern_cls, PipelinePattern):
        raise DefinitionBuildError("Registry entry for 'pipeline' is not PipelinePattern")
    try:
        config = PipelineConfig.from_options(flow.options)
    except ValueError as exc:
        raise DefinitionBuildError(str(exc)) from exc
    return pattern_cls(
        name=flow.name,
        config=config,
        resource_engine=context.resource_engine,
    )
