"""
SelectorNode – classic "OR" / Fallback composite.

Tries children left to right. Succeeds on the first SUCCESS.
Only fails if every child fails.

This module is part of Palm's general-purpose Behavior Tree Engine and must remain
completely independent of any wizard, UI, persistence, or domain concerns.
"""

from __future__ import annotations

from ...base import BaseNode, Blackboard, NodeStatus
from ...composite import CompositeNode


class SelectorNode(CompositeNode):
    """
    Selector (OR / Fallback) composite.

    Execution rules:
    - Try children in order.
    - Return SUCCESS on the first child that succeeds.
    - Propagate RUNNING / WAITING_FOR_INPUT from the current child.
    - Only when the last child fails do we return FAILURE.
    - Empty selector → FAILURE (no alternative succeeded).

    Stateful across ticks via `_current_index` (same pattern as Sequence).
    """

    def __init__(self, name: str, children: list[BaseNode] | None = None) -> None:
        super().__init__(name, children)
        self._current_index: int = 0

    def _tick_impl(self, blackboard: Blackboard) -> NodeStatus:
        if not self.children:
            return NodeStatus.FAILURE

        while self._current_index < len(self.children):
            child = self.children[self._current_index]
            status = child.tick(blackboard)

            if status in (NodeStatus.RUNNING, NodeStatus.WAITING_FOR_INPUT):
                return status

            if status == NodeStatus.SUCCESS:
                self._current_index = 0
                return NodeStatus.SUCCESS

            # FAILURE of this child → try next alternative
            self._current_index += 1

        # All alternatives failed
        self._current_index = 0
        return NodeStatus.FAILURE

    def _reset_impl(self) -> None:
        self._current_index = 0

    def __repr__(self) -> str:
        return (
            f"SelectorNode(name={self.name!r}, "
            f"current={self._current_index}/{len(self.children)})"
        )
