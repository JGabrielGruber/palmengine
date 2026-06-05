"""
WorkflowExecutor - placeholder for future non-interactive DAG execution.
"""

from __future__ import annotations

from typing import Any

from .dag import DAG


class WorkflowExecutor:
    """Executes a DAG (future implementation)."""

    def __init__(self) -> None:
        self.results: dict[str, Any] = {}

    def run(self, dag: DAG, initial_context: dict[str, Any] | None = None) -> dict[str, Any]:
        """Stub implementation."""
        order = dag.topological()
        context = dict(initial_context or {})
        for node_id in order:
            node = dag.nodes[node_id]
            if node.func:
                self.results[node_id] = node.func(context)
                context[node_id] = self.results[node_id]
            else:
                self.results[node_id] = None
        return self.results
