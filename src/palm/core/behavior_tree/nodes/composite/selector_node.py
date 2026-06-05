"""SelectorNode — OR / fallback composite."""

from __future__ import annotations

from palm.core.behavior_tree.base import BaseNode
from palm.core.behavior_tree.base_pattern import PatternStatus
from palm.core.behavior_tree.composite import CompositeNode
from palm.core.context import BaseState


class SelectorNode(CompositeNode):
    """Tries children in order; succeeds on first success."""

    def __init__(self, name: str, children: list[BaseNode] | None = None) -> None:
        super().__init__(name, children)
        self._current_index = 0

    def _tick_impl(self, state: BaseState) -> PatternStatus:
        if not self.children:
            return PatternStatus.FAILURE

        while self._current_index < len(self.children):
            status = self.children[self._current_index].tick(state)
            if status in (PatternStatus.RUNNING, PatternStatus.WAITING_FOR_INPUT):
                return status
            if status == PatternStatus.SUCCESS:
                self._current_index = 0
                return PatternStatus.SUCCESS
            self._current_index += 1

        self._current_index = 0
        return PatternStatus.FAILURE

    def _reset_impl(self) -> None:
        self._current_index = 0
