"""
Parallel pattern app manifest — declares Palm layer dependencies and registry hooks.

Read this file first to understand which Palm subsystems the parallel pattern dogfoods.
"""

from __future__ import annotations

from palm.common.patterns.app import PatternApp


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
    )


parallel_app = ParallelApp()

__all__ = ["ParallelApp", "parallel_app"]