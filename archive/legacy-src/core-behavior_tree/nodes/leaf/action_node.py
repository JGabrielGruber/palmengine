"""
ActionNode – a leaf that performs a side-effect or computation.

The action callable receives the blackboard and may return a NodeStatus or None
(None is treated as SUCCESS).

This module is part of Palm's general-purpose Behavior Tree Engine and must remain
completely independent of any wizard, UI, persistence, or domain concerns.
"""

from __future__ import annotations

from collections.abc import Callable

from ...base import Blackboard, NodeStatus
from ...leaf import LeafNode


class ActionNode(LeafNode):
    """
    Leaf node that executes an arbitrary side-effect or computation.

    The provided `action` callable has the signature:

        def action(blackboard: Blackboard) -> NodeStatus | None

    - If the callable returns None or NodeStatus.SUCCESS → the node succeeds.
    - Returning NodeStatus.FAILURE or RUNNING / WAITING is respected.
    - Any exception raised by the callable is turned into NodeExecutionError
      by the BaseNode tick wrapper.

    Example:
        def write_log(bb: Blackboard):
            print("Current data:", bb.snapshot())
            bb.set("last_action", "wrote_log")

        node = ActionNode("log_step", action=write_log)
    """

    def __init__(
        self,
        name: str,
        action: Callable[[Blackboard], NodeStatus | None],
    ) -> None:
        super().__init__(name)
        if not callable(action):
            raise TypeError("ActionNode requires a callable for 'action'")
        self._action = action

    def _tick_impl(self, blackboard: Blackboard) -> NodeStatus:
        result = self._action(blackboard)
        if result is None:
            return NodeStatus.SUCCESS
        if isinstance(result, NodeStatus):
            return result
        # Defensive: treat unexpected returns as failure rather than crashing
        return NodeStatus.FAILURE

    def __repr__(self) -> str:
        return f"ActionNode(name={self.name!r})"
