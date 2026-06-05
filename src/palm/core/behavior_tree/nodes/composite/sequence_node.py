"""SequenceNode — AND composite."""

from __future__ import annotations

from palm.core.behavior_tree.base import BaseNode
from palm.core.behavior_tree.base_pattern import PatternStatus
from palm.core.behavior_tree.blackboard import Blackboard
from palm.core.behavior_tree.composite import CompositeNode


class SequenceNode(CompositeNode):
    """Runs children in order; succeeds when all succeed."""

    def __init__(self, name: str, children: list[BaseNode] | None = None) -> None:
        super().__init__(name, children)
        self._current_index = 0

    def _tick_impl(self, blackboard: Blackboard) -> PatternStatus:
        if not self.children:
            return PatternStatus.SUCCESS

        while self._current_index < len(self.children):
            status = self.children[self._current_index].tick(blackboard)
            if status in (PatternStatus.RUNNING, PatternStatus.WAITING_FOR_INPUT):
                return status
            if status == PatternStatus.FAILURE:
                self._current_index = 0
                return PatternStatus.FAILURE
            self._current_index += 1

        self._current_index = 0
        return PatternStatus.SUCCESS

    def _reset_impl(self) -> None:
        self._current_index = 0