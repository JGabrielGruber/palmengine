"""RepeatNode — repeats its child a fixed or unbounded number of times."""

from __future__ import annotations

from palm.core.behavior_tree.base import BaseNode
from palm.core.behavior_tree.base_pattern import PatternStatus
from palm.core.behavior_tree.decorator import DecoratorNode
from palm.core.context import BaseState


class RepeatNode(DecoratorNode):
    def __init__(self, name: str, child: BaseNode, times: int | None = None) -> None:
        super().__init__(name, child=child)
        if times is not None and times < 1:
            raise ValueError("RepeatNode times must be None or >= 1")
        self.times = times
        self._count = 0

    def _tick_impl(self, state: BaseState) -> PatternStatus:
        while True:
            if self.times is not None and self._count >= self.times:
                self._count = 0
                return PatternStatus.SUCCESS

            status = self.child.tick(state)
            if status in (PatternStatus.RUNNING, PatternStatus.WAITING_FOR_INPUT):
                return status
            if status == PatternStatus.FAILURE:
                self._count = 0
                return PatternStatus.FAILURE

            self._count += 1
            if self.times is not None and self._count >= self.times:
                self._count = 0
                return PatternStatus.SUCCESS

    def _reset_impl(self) -> None:
        self._count = 0