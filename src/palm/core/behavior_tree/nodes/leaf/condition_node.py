"""ConditionNode — leaf that evaluates a predicate."""

from __future__ import annotations

from collections.abc import Callable

from palm.core.behavior_tree.base_pattern import PatternStatus
from palm.core.behavior_tree.leaf import LeafNode
from palm.core.state import BaseState


class ConditionNode(LeafNode):
    """Returns SUCCESS when ``predicate(state)`` is truthy."""

    def __init__(
        self,
        name: str,
        predicate: Callable[[BaseState], bool],
    ) -> None:
        super().__init__(name)
        if not callable(predicate):
            raise TypeError("ConditionNode requires a callable predicate")
        self._predicate = predicate

    def _tick_impl(self, state: BaseState) -> PatternStatus:
        return (
            PatternStatus.SUCCESS
            if self._predicate(state)
            else PatternStatus.FAILURE
        )