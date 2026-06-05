"""RootNode — canonical entry point for a behavior tree."""

from __future__ import annotations

from palm.core.behavior_tree.base import BaseNode
from palm.core.behavior_tree.base_pattern import PatternStatus
from palm.core.behavior_tree.decorator import DecoratorNode
from palm.core.context import BaseState


class RootNode(DecoratorNode):
    """Named root wrapper that validates the full tree at construction."""

    def __init__(self, name: str, child: BaseNode) -> None:
        super().__init__(name, child=child)
        self.validate_tree_structure()

    def _tick_impl(self, state: BaseState) -> PatternStatus:
        return self.child.tick(state)