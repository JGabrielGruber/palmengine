"""
Parallel pattern app manifest — declares Palm layer dependencies and registry hooks.

Read this file first to understand which Palm subsystems the parallel pattern dogfoods.
"""

from __future__ import annotations

from palm.common.patterns.app import PatternApp
from palm.patterns._registry import McpContributor, register_mcp_contributor
from palm.patterns.parallel.bindings.mcp import register_parallel_mcp_tools


class ParallelApp(PatternApp):
    name = "parallel"
    label = "Parallel branch execution"
    palm_layers = (
        "core.behavior_tree",
        "core.context",
        "core.event",
        "core.orchestration",
        "common.patterns",
        "common.persistence",
        "common.state",
        "definitions.flow",
        "instances",
    )
    registry_hooks = (
        "builder",
        "instance_sync",
        "submission_metadata",
        "mcp_contributor",
    )

    def ready(self) -> None:
        register_mcp_contributor(
            McpContributor(pattern_name="parallel", register=register_parallel_mcp_tools)
        )


parallel_app = ParallelApp()

__all__ = ["ParallelApp", "parallel_app"]
