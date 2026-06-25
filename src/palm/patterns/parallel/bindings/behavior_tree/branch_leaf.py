"""
BranchLeaf — behavior-tree leaf that runs one isolated sub-workflow branch.
"""

from __future__ import annotations

from palm.core.behavior_tree.base_pattern import PatternStatus
from palm.core.behavior_tree.leaf import LeafNode
from palm.core.context import BaseState
from palm.patterns.parallel.flow.branch import BranchRunner


class BranchLeaf(LeafNode):
    """Ticks a :class:`~palm.patterns.parallel.flow.branch.BranchRunner` each visit."""

    def __init__(self, runner: BranchRunner) -> None:
        super().__init__(runner.branch.slug)
        self._runner = runner

    @property
    def runner(self) -> BranchRunner:
        return self._runner

    def _tick_impl(self, state: BaseState) -> PatternStatus:
        if self._runner.completed:
            return PatternStatus.SUCCESS
        return self._runner.tick(state)
