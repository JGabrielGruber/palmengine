"""RetryNode — retries its child on FAILURE."""

from __future__ import annotations

from palm.core.behavior_tree.base import BaseNode
from palm.core.behavior_tree.base_pattern import PatternStatus
from palm.core.behavior_tree.blackboard import Blackboard
from palm.core.behavior_tree.decorator import DecoratorNode


class RetryNode(DecoratorNode):
    def __init__(self, name: str, child: BaseNode, max_attempts: int = 3) -> None:
        super().__init__(name, child=child)
        if max_attempts < 1:
            raise ValueError("RetryNode max_attempts must be >= 1")
        self.max_attempts = max_attempts
        self._attempts = 0

    def _tick_impl(self, blackboard: Blackboard) -> PatternStatus:
        while True:
            status = self.child.tick(blackboard)
            if status in (PatternStatus.RUNNING, PatternStatus.WAITING_FOR_INPUT):
                return status
            if status == PatternStatus.SUCCESS:
                self._attempts = 0
                return PatternStatus.SUCCESS
            self._attempts += 1
            if self._attempts >= self.max_attempts:
                self._attempts = 0
                return PatternStatus.FAILURE

    def _reset_impl(self) -> None:
        self._attempts = 0