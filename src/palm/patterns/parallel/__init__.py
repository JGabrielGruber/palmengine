"""
Parallel pattern app — scoped branches, sub-workflows, and merge strategies.
"""

from palm.patterns.parallel import registry as registry  # — side effect
from palm.patterns.parallel.bindings.context.keys import ParallelKeys
from palm.patterns.parallel.bindings.definitions.builder import build, parallel_config_from_options
from palm.patterns.parallel.bindings.definitions.config import (
    BranchConfig,
    MergeStrategy,
    ParallelConfig,
)
from palm.patterns.parallel.flow.branch import BranchRunner
from palm.patterns.parallel.flow.merge import get_branch_results, merge_branch_results
from palm.patterns.parallel.pattern import ParallelPattern

__all__ = [
    "BranchConfig",
    "BranchRunner",
    "MergeStrategy",
    "ParallelConfig",
    "ParallelKeys",
    "ParallelPattern",
    "build",
    "get_branch_results",
    "merge_branch_results",
    "parallel_config_from_options",
    "registry",
]
