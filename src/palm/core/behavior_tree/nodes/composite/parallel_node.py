"""ParallelNode — ticks all children each tick until terminal."""

from __future__ import annotations

from enum import StrEnum

from palm.core.behavior_tree.base import BaseNode
from palm.core.behavior_tree.base_pattern import PatternStatus
from palm.core.behavior_tree.composite import CompositeNode
from palm.core.context import BaseState


class ParallelPolicy(StrEnum):
    SUCCESS_ON_ALL = "success_on_all"
    SUCCESS_ON_ANY = "success_on_any"


class ParallelNode(CompositeNode):
    """Parallel composite with configurable success policy."""

    def __init__(
        self,
        name: str,
        children: list[BaseNode] | None = None,
        policy: ParallelPolicy = ParallelPolicy.SUCCESS_ON_ALL,
    ) -> None:
        super().__init__(name, children)
        self.policy = policy
        self._child_results: list[PatternStatus | None] = [None] * len(self.children)

    def _tick_impl(self, state: BaseState) -> PatternStatus:
        if not self.children:
            return PatternStatus.SUCCESS

        any_waiting = False
        any_running = False

        for idx, child in enumerate(self.children):
            if self._child_results[idx] is not None:
                continue
            status = child.tick(state)
            if status in (PatternStatus.RUNNING, PatternStatus.WAITING_FOR_INPUT):
                if status == PatternStatus.WAITING_FOR_INPUT:
                    any_waiting = True
                else:
                    any_running = True
                continue
            self._child_results[idx] = status
            if self.policy == ParallelPolicy.SUCCESS_ON_ANY and status == PatternStatus.SUCCESS:
                self._child_results = [PatternStatus.SUCCESS] * len(self.children)
                return PatternStatus.SUCCESS
            if status == PatternStatus.FAILURE and self.policy == ParallelPolicy.SUCCESS_ON_ALL:
                return PatternStatus.FAILURE

        if any_waiting:
            return PatternStatus.WAITING_FOR_INPUT
        if any_running:
            return PatternStatus.RUNNING

        successes = sum(1 for r in self._child_results if r == PatternStatus.SUCCESS)
        failures = sum(1 for r in self._child_results if r == PatternStatus.FAILURE)

        if self.policy == ParallelPolicy.SUCCESS_ON_ALL:
            if failures > 0:
                return PatternStatus.FAILURE
            return (
                PatternStatus.SUCCESS
                if successes == len(self.children)
                else PatternStatus.FAILURE
            )
        if successes > 0:
            return PatternStatus.SUCCESS
        return PatternStatus.FAILURE

    def _reset_impl(self) -> None:
        self._child_results = [None] * len(self.children)