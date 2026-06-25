"""Parallel definition bindings — builder and configuration."""

from palm.patterns.parallel.bindings.definitions.builder import build, parallel_config_from_options
from palm.patterns.parallel.bindings.definitions.config import (
    BranchConfig,
    MergeStrategy,
    ParallelConfig,
)

__all__ = [
    "BranchConfig",
    "MergeStrategy",
    "ParallelConfig",
    "build",
    "parallel_config_from_options",
]