"""
DAG pattern app manifest — resource-node graphs with dependencies (0.54.3).
"""

from __future__ import annotations

from palm.common.patterns.app import PatternApp


class DagApp(PatternApp):
    name = "dag"
    label = "Directed acyclic graph of resource nodes"
    palm_layers = (
        "core.behavior_tree",
        "core.context",
        "core.resource",
        "common.patterns",
        "definitions.flow",
    )
    registry_hooks = ("builder",)


dag_app = DagApp()

__all__ = ["DagApp", "dag_app"]
