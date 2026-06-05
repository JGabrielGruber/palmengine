"""ActionNode — leaf that runs a callable side effect."""

from __future__ import annotations

from collections.abc import Callable

from palm.core.behavior_tree.base_pattern import PatternStatus
from palm.core.behavior_tree.leaf import LeafNode
from palm.core.state import BaseState


class ActionNode(LeafNode):
    """Executes ``action(state)`` and maps the result to a status."""

    def __init__(
        self,
        name: str,
        action: Callable[[BaseState], PatternStatus | None],
    ) -> None:
        super().__init__(name)
        if not callable(action):
            raise TypeError("ActionNode requires a callable action")
        self._action = action

    def _tick_impl(self, state: BaseState) -> PatternStatus:
        result = self._action(state)
        if result is None:
            return PatternStatus.SUCCESS
        if isinstance(result, PatternStatus):
            return result
        return PatternStatus.FAILURE