"""
ETL pattern — extract, transform, load pipelines.

Registers as ``"etl"`` in ``pattern_registry``.
"""

from __future__ import annotations

from typing import Any

from palm.core.behavior_tree import BasePattern, PatternStatus
from palm.core.registry import pattern_registry


class EtlPattern(BasePattern):
    """Placeholder ETL pattern: marks pipeline phase on blackboard."""

    def __init__(self, *, name: str = "etl") -> None:
        super().__init__(name=name)
        self._phase = 0
        self._phases = ("extract", "transform", "load")

    def tick(self, blackboard: dict[str, Any]) -> PatternStatus:
        if self._phase >= len(self._phases):
            return PatternStatus.SUCCESS
        blackboard["etl_phase"] = self._phases[self._phase]
        self._phase += 1
        if self._phase >= len(self._phases):
            return PatternStatus.SUCCESS
        return PatternStatus.RUNNING


pattern_registry.register("etl", EtlPattern)
