"""
Build behavior-tree structures for parallel flows.
"""

from __future__ import annotations

from palm.core.behavior_tree import ParallelNode, RootNode
from palm.patterns.parallel.branch import BranchRunner
from palm.patterns.parallel.branch_leaf import BranchLeaf
from palm.patterns.parallel.config import ParallelConfig


def build_parallel_tree(
    name: str,
    config: ParallelConfig,
    runners: list[BranchRunner],
) -> tuple[RootNode, ParallelNode]:
    """Return ``(root, parallel)`` for the configured branches."""
    leaves = [BranchLeaf(runner) for runner in runners]
    parallel = ParallelNode(
        f"{name}_parallel",
        children=leaves,
        policy=config.parallel_policy,
    )
    root = RootNode(f"{name}_root", child=parallel)
    return root, parallel