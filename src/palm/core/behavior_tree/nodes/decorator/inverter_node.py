"""InverterNode — flips SUCCESS and FAILURE."""

from __future__ import annotations

from palm.core.behavior_tree.base import BaseNode
from palm.core.behavior_tree.base_pattern import PatternStatus
from palm.core.behavior_tree.decorator import DecoratorNode
from palm.core.context import BaseState


class InverterNode(DecoratorNode):
    def __init__(self, name: str, child: BaseNode) -> None:
        super().__init__(name, child=child)

    def _tick_impl(self, state: BaseState) -> PatternStatus:
        status = self.child.tick(state)
        if status == PatternStatus.SUCCESS:
            return PatternStatus.FAILURE
        if status == PatternStatus.FAILURE:
            return PatternStatus.SUCCESS
        return status