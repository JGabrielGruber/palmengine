"""
SequenceNode – classic "AND" composite.

Runs children left to right. Succeeds only when every child succeeds.
Remembers the last running child across ticks so that long-running or
WAITING children resume correctly.

This module is part of Palm's general-purpose Behavior Tree Engine and must remain
completely independent of any wizard, UI, persistence, or domain concerns.
"""

from __future__ import annotations

from ...base import BaseNode, Blackboard, NodeStatus
from ...composite import CompositeNode


class SequenceNode(CompositeNode):
    """
    Sequence (AND) composite.

    Execution rules:
    - Execute children in definition order.
    - On first FAILURE → immediately return FAILURE (fail-fast) and reset index.
    - On RUNNING or WAITING_FOR_INPUT → remember index and return that status.
    - Only when the final child returns SUCCESS do we reset the index and return SUCCESS.
    - Empty sequence → SUCCESS (vacuous truth, consistent with many BT libs).

    The node is stateful: `_current_index` survives across ticks until a terminal
    result or explicit reset().
    """

    def __init__(self, name: str, children: list[BaseNode] | None = None) -> None:
        super().__init__(name, children)
        self._current_index: int = 0

    def _tick_impl(self, blackboard: Blackboard) -> NodeStatus:
        if not self.children:
            return NodeStatus.SUCCESS

        while self._current_index < len(self.children):
            child = self.children[self._current_index]
            status = child.tick(blackboard)

            if status in (NodeStatus.RUNNING, NodeStatus.WAITING_FOR_INPUT):
                return status

            if status == NodeStatus.FAILURE:
                self._current_index = 0
                return NodeStatus.FAILURE

            # SUCCESS — advance to next sibling
            self._current_index += 1

        # All children succeeded
        self._current_index = 0
        return NodeStatus.SUCCESS

    def _reset_impl(self) -> None:
        self._current_index = 0

    def __repr__(self) -> str:
        return (
            f"SequenceNode(name={self.name!r}, "
            f"current={self._current_index}/{len(self.children)})"
        )
