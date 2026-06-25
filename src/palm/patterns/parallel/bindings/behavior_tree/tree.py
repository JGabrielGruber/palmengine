"""
Build behavior-tree structures for parallel flows.
"""

from __future__ import annotations

from typing import cast

from palm.core.behavior_tree import BaseNode, ParallelNode, RootNode
from palm.patterns.parallel.bindings.behavior_tree.branch_leaf import BranchLeaf
from palm.patterns.parallel.bindings.definitions.config import ParallelConfig
from palm.patterns.parallel.flow.branch import BranchRunner


def build_parallel_tree(
    name: str,
    config: ParallelConfig,
    runners: list[BranchRunner],
) -> tuple[RootNode, ParallelNode]:
    """Return ``(root, parallel)`` for the configured branches."""
    leaves = [BranchLeaf(runner) for runner in runners]
    parallel = ParallelNode(
        f"{name}_parallel",
        children=cast(list[BaseNode], leaves),
        policy=config.parallel_policy,
    )
    root = RootNode(f"{name}_root", child=parallel)
    return root, parallel
