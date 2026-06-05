"""
RetryNode – decorator that retries its child on FAILURE up to a maximum number of attempts.

This module is part of Palm's general-purpose Behavior Tree Engine and must remain
completely independent of any wizard, UI, persistence, or domain concerns.
"""

from __future__ import annotations

from ...base import BaseNode, Blackboard, NodeStatus
from ...decorator import DecoratorNode


class RetryNode(DecoratorNode):
    """
    Retries the child on FAILURE.

    - On child SUCCESS → return SUCCESS immediately (reset attempt counter).
    - On child RUNNING / WAITING → propagate.
    - On child FAILURE → increment attempt counter. If attempts < max_attempts,
      tick the child again on the next visit. When attempts are exhausted,
      return FAILURE.

    This is the classic "retry on transient failure" pattern.
    """

    def __init__(self, name: str, child: BaseNode, max_attempts: int = 3) -> None:
        super().__init__(name, child=child)
        if max_attempts < 1:
            raise ValueError("RetryNode max_attempts must be >= 1")
        self.max_attempts: int = max_attempts
        self._attempts: int = 0

    def _tick_impl(self, blackboard: Blackboard) -> NodeStatus:
        while True:
            status = self.child.tick(blackboard)

            if status in (NodeStatus.RUNNING, NodeStatus.WAITING_FOR_INPUT):
                return status

            if status == NodeStatus.SUCCESS:
                self._attempts = 0
                return NodeStatus.SUCCESS

            # FAILURE
            self._attempts += 1
            if self._attempts >= self.max_attempts:
                self._attempts = 0
                return NodeStatus.FAILURE

            # Otherwise we will immediately retry the child in the next
            # iteration of this while (same tick). This gives "eager" retry
            # within a single parent tick, which is usually desirable.

    def _reset_impl(self) -> None:
        self._attempts = 0

    def __repr__(self) -> str:
        return f"RetryNode(name={self.name!r}, " f"attempts={self._attempts}/{self.max_attempts})"
