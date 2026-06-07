"""
DAG pattern implementation — directed acyclic workflow execution.
"""

from __future__ import annotations

from palm.core.behavior_tree import BasePattern, PatternStatus
from palm.core.context import BaseState


class DagPattern(BasePattern):
    """Placeholder DAG pattern: single-pass completion."""

    def __init__(self, *, name: str = "dag") -> None:
        super().__init__(name=name)

    def tick(self, state: BaseState) -> PatternStatus:
        if state.get("dag_complete"):
            return PatternStatus.SUCCESS
        state.set("dag_complete", True)
        return PatternStatus.SUCCESS