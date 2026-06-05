"""
WorkflowRegistry - central registry for non-interactive workflows (future).
"""

from __future__ import annotations

from .dag import DAG


class WorkflowRegistry:
    """Simple in-memory registry."""

    def __init__(self) -> None:
        self._workflows: dict[str, DAG] = {}

    def register(self, dag: DAG) -> None:
        self._workflows[dag.name] = dag

    def get(self, name: str) -> DAG:
        if name not in self._workflows:
            raise KeyError(f"Workflow '{name}' not registered")
        return self._workflows[name]

    def list(self) -> list[str]:
        return list(self._workflows.keys())
