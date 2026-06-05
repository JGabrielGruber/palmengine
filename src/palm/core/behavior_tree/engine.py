"""
Behavior Tree engine — general-purpose control-flow execution.

Runs registered ``BasePattern`` trees with a shared blackboard. Independent of
wizards, CLI, persistence, and all other engines.
"""

from __future__ import annotations

from typing import Any

from palm.core.base import BasePalmEngine
from palm.core.behavior_tree.base_pattern import BasePattern, PatternStatus


class BehaviorTreeEngine(BasePalmEngine):
    """Executes a behavior tree rooted at a single ``BasePattern``."""

    def __init__(self) -> None:
        super().__init__(name="behavior_tree")
        self._root: BasePattern | None = None
        self._blackboard: dict[str, Any] = {}

    @property
    def blackboard(self) -> dict[str, Any]:
        return self._blackboard

    def set_root(self, root: BasePattern) -> None:
        self._root = root

    def tick(self) -> PatternStatus:
        if self._root is None:
            return PatternStatus.FAILURE
        return self._root.tick(self._blackboard)

    def _do_initialize(self, **options: Any) -> None:
        initial = options.get("blackboard")
        if isinstance(initial, dict):
            self._blackboard = dict(initial)

    def _do_shutdown(self) -> None:
        self._blackboard.clear()
        self._root = None
