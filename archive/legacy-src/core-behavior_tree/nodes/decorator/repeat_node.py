"""
RepeatNode – decorator that executes its child a fixed number of times (or until failure).

This module is part of Palm's general-purpose Behavior Tree Engine and must remain
completely independent of any wizard, UI, persistence, or domain concerns.
"""

from __future__ import annotations

from ...base import BaseNode, Blackboard, NodeStatus
from ...decorator import DecoratorNode


class RepeatNode(DecoratorNode):
    """
    Repeats the child node a given number of times.

    Behavior:
    - If `times` is None: repeat forever until the child returns FAILURE
      (then the Repeat returns FAILURE). Useful for "keep trying" loops.
    - If `times` is an int > 0: run the child exactly that many times
      (or until it fails). After successful completion of N runs, return SUCCESS.
    - RUNNING / WAITING from child are always propagated.

    The repeat counter is reset on explicit `reset()` or after terminal result.
    """

    def __init__(self, name: str, child: BaseNode, times: int | None = None) -> None:
        super().__init__(name, child=child)
        if times is not None and times < 1:
            raise ValueError("RepeatNode 'times' must be None or >= 1")
        self.times: int | None = times
        self._count: int = 0

    def _tick_impl(self, blackboard: Blackboard) -> NodeStatus:
        while True:
            if self.times is not None and self._count >= self.times:
                self._count = 0
                return NodeStatus.SUCCESS

            status = self.child.tick(blackboard)

            if status in (NodeStatus.RUNNING, NodeStatus.WAITING_FOR_INPUT):
                return status

            if status == NodeStatus.FAILURE:
                self._count = 0
                return NodeStatus.FAILURE

            # SUCCESS from child
            self._count += 1

            if self.times is not None and self._count >= self.times:
                self._count = 0
                return NodeStatus.SUCCESS

            # Otherwise continue looping (for the "forever until failure" case)

    def _reset_impl(self) -> None:
        self._count = 0

    def __repr__(self) -> str:
        target = "∞" if self.times is None else str(self.times)
        return f"RepeatNode(name={self.name!r}, target={target}, count={self._count})"
