"""
DAG pattern app manifest — declares Palm layer dependencies and registry hooks.

Execution logic is still a placeholder; ``flow/`` is reserved for graph scheduling.
"""

from __future__ import annotations

from palm.common.patterns.app import PatternApp


class DagApp(PatternApp):
    name = "dag"
    label = "Directed acyclic graph"
    palm_layers = (
        "core.behavior_tree",
        "core.context",
        "common.patterns",
        "definitions.flow",
    )
    registry_hooks = ("builder",)


dag_app = DagApp()

__all__ = ["DagApp", "dag_app"]
