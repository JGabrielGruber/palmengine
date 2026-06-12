"""
Parallel pattern app — scoped branches, sub-workflows, and merge strategies.
"""

from palm.patterns.parallel import registry as registry  # noqa: F401 — side effect
from palm.patterns.parallel.branch import BranchRunner
from palm.patterns.parallel.builder import build, parallel_config_from_options
from palm.patterns.parallel.config import BranchConfig, MergeStrategy, ParallelConfig
from palm.patterns.parallel.keys import ParallelKeys
from palm.patterns.parallel.merge import get_branch_results, merge_branch_results
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