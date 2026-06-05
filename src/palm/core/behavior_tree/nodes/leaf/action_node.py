"""ActionNode — leaf that runs a callable side effect."""

from __future__ import annotations

from collections.abc import Callable

from palm.core.behavior_tree.base_pattern import PatternStatus
from palm.core.behavior_tree.blackboard import Blackboard
from palm.core.behavior_tree.leaf import LeafNode


class ActionNode(LeafNode):
    """Executes ``action(blackboard)`` and maps the result to a status."""

    def __init__(
        self,
        name: str,
        action: Callable[[Blackboard], PatternStatus | None],
    ) -> None:
        super().__init__(name)
        if not callable(action):
            raise TypeError("ActionNode requires a callable action")
        self._action = action

    def _tick_impl(self, blackboard: Blackboard) -> PatternStatus:
        result = self._action(blackboard)
        if result is None:
            return PatternStatus.SUCCESS
        if isinstance(result, PatternStatus):
            return result
        return PatternStatus.FAILURE