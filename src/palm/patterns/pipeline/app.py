"""
Pipeline pattern app manifest — declares Palm layer dependencies and registry hooks.
"""

from __future__ import annotations

from palm.common.patterns.app import PatternApp
from palm.patterns._registry import McpContributor, register_mcp_contributor
from palm.patterns.pipeline.bindings.mcp import register_pipeline_mcp_tools


class PipelineApp(PatternApp):
    name = "pipeline"
    label = "Sequential pipeline"
    palm_layers = (
        "core.behavior_tree",
        "core.context",
        "core.transform",
        "common.patterns",
        "common.transforms",
        "definitions.flow",
    )
    registry_hooks = ("builder", "mcp_contributor")

    def ready(self) -> None:
        register_mcp_contributor(
            McpContributor(pattern_name="pipeline", register=register_pipeline_mcp_tools)
        )


pipeline_app = PipelineApp()

__all__ = ["PipelineApp", "pipeline_app"]