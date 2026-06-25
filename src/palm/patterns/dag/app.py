"""DAG pattern app manifest."""

from __future__ import annotations

from palm.common.patterns.app import PatternApp


class DagApp(PatternApp):
    name = "dag"
    label = "Directed acyclic graph"


dag_app = DagApp()

__all__ = ["DagApp", "dag_app"]