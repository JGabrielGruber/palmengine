"""
ParallelNode – composite that ticks multiple children "simultaneously".

On every tick the node ticks all non-terminal children. Success/failure policy
is configurable.

This module is part of Palm's general-purpose Behavior Tree Engine and must remain
completely independent of any wizard, UI, persistence, or domain concerns.
"""

from __future__ import annotations

from enum import StrEnum

from ...base import BaseNode, Blackboard, NodeStatus
from ...composite import CompositeNode


class ParallelPolicy(StrEnum):
    """Policies controlling when a ParallelNode reports terminal status."""

    SUCCESS_ON_ALL = "SUCCESS_ON_ALL"  # All children must succeed (default)
    SUCCESS_ON_ANY = "SUCCESS_ON_ANY"  # Any child success makes the parallel succeed


class ParallelNode(CompositeNode):
    """
    Parallel composite.

    Every tick, the node visits every child that has not yet reached a terminal
    status. It collects SUCCESS/FAILURE results and decides according to the policy.

    - Children that return RUNNING or WAITING are left running.
    - The node itself returns RUNNING (or WAITING if any child is waiting) while
      work remains.
    - Policy SUCCESS_ON_ALL: the parallel succeeds only when every child has
      succeeded. First child FAILURE fails the whole parallel.
    - Policy SUCCESS_ON_ANY: first SUCCESS from any child succeeds the parallel.

    This implementation is intentionally simple (no true OS threads). It gives
    the appearance of concurrent execution within a single-threaded tick loop.
    """

    def __init__(
        self,
        name: str,
        children: list[BaseNode] | None = None,
        policy: ParallelPolicy = ParallelPolicy.SUCCESS_ON_ALL,
    ) -> None:
        super().__init__(name, children)
        self.policy: ParallelPolicy = policy
        # Track terminal outcomes per child index (None while still active)
        self._child_results: list[NodeStatus | None] = [None] * len(self.children)

    def _tick_impl(self, blackboard: Blackboard) -> NodeStatus:
        if not self.children:
            return NodeStatus.SUCCESS

        any_waiting = False
        any_running = False

        for idx, child in enumerate(self.children):
            if self._child_results[idx] is not None:
                continue  # already terminal

            status = child.tick(blackboard)

            if status in (NodeStatus.RUNNING, NodeStatus.WAITING_FOR_INPUT):
                if status == NodeStatus.WAITING_FOR_INPUT:
                    any_waiting = True
                else:
                    any_running = True
                continue

            # Terminal result
            self._child_results[idx] = status

            if self.policy == ParallelPolicy.SUCCESS_ON_ANY and status == NodeStatus.SUCCESS:
                self._child_results = [NodeStatus.SUCCESS] * len(self.children)
                return NodeStatus.SUCCESS

            if status == NodeStatus.FAILURE and self.policy == ParallelPolicy.SUCCESS_ON_ALL:
                # Fail fast on first failure under ALL policy
                return NodeStatus.FAILURE

        # Re-evaluate overall status
        if any_waiting:
            return NodeStatus.WAITING_FOR_INPUT
        if any_running:
            return NodeStatus.RUNNING

        # All children have reported terminal results
        successes = sum(1 for r in self._child_results if r == NodeStatus.SUCCESS)
        failures = sum(1 for r in self._child_results if r == NodeStatus.FAILURE)

        if self.policy == ParallelPolicy.SUCCESS_ON_ALL:
            if failures > 0:
                return NodeStatus.FAILURE
            return NodeStatus.SUCCESS if successes == len(self.children) else NodeStatus.FAILURE

        # SUCCESS_ON_ANY
        if successes > 0:
            return NodeStatus.SUCCESS
        return NodeStatus.FAILURE

    def _reset_impl(self) -> None:
        self._child_results = [None] * len(self.children)

    def __repr__(self) -> str:
        done = sum(1 for r in self._child_results if r is not None)
        return f"ParallelNode(name={self.name!r}, policy={self.policy}, done={done}/{len(self.children)})"
