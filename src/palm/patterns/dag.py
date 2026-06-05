"""
DAG pattern — directed acyclic workflow execution.

Registers as ``"dag"`` in ``pattern_registry``.
"""

from __future__ import annotations

from typing import Any

from palm.core.behavior_tree import BasePattern, PatternStatus
from palm.core.registry import pattern_registry


class DagPattern(BasePattern):
    """Placeholder DAG pattern: single-pass completion."""

    def __init__(self, *, name: str = "dag") -> None:
        super().__init__(name=name)

    def tick(self, blackboard: dict[str, Any]) -> PatternStatus:
        if blackboard.get("dag_complete"):
            return PatternStatus.SUCCESS
        blackboard["dag_complete"] = True
        return PatternStatus.SUCCESS


pattern_registry.register("dag", DagPattern)
