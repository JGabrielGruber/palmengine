"""
Parallel pattern app — scoped branches, sub-workflows, and merge strategies.
"""

from plugins.patterns.parallel import registry as registry  # — side effect
from plugins.patterns.parallel.bindings.context.keys import ParallelKeys
from plugins.patterns.parallel.bindings.definitions.builder import build, parallel_config_from_options
from plugins.patterns.parallel.bindings.definitions.config import (
    BranchConfig,
    MergeStrategy,
    ParallelConfig,
)
from plugins.patterns.parallel.flow.branch import BranchRunner
from plugins.patterns.parallel.flow.merge import get_branch_results, merge_branch_results
from plugins.patterns.parallel.pattern import ParallelPattern

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
