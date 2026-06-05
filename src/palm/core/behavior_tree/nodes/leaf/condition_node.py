"""ConditionNode — leaf that evaluates a predicate."""

from __future__ import annotations

from collections.abc import Callable

from palm.core.behavior_tree.base_pattern import PatternStatus
from palm.core.behavior_tree.blackboard import Blackboard
from palm.core.behavior_tree.leaf import LeafNode


class ConditionNode(LeafNode):
    """Returns SUCCESS when ``predicate(blackboard)`` is truthy."""

    def __init__(
        self,
        name: str,
        predicate: Callable[[Blackboard], bool],
    ) -> None:
        super().__init__(name)
        if not callable(predicate):
            raise TypeError("ConditionNode requires a callable predicate")
        self._predicate = predicate

    def _tick_impl(self, blackboard: Blackboard) -> PatternStatus:
        return (
            PatternStatus.SUCCESS
            if self._predicate(blackboard)
            else PatternStatus.FAILURE
        )