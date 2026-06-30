"""Parallel flow coordination — branch execution, scoping, and merge."""

from palm.patterns.parallel.flow.branch import BranchRunner
from palm.patterns.parallel.flow.merge import (
    get_branch_results,
    merge_branch_results,
    record_branch_result,
)
from palm.patterns.parallel.flow.scope import (
    enter_branch,
    leave_branch,
    load_branch_snapshot,
    load_branch_snapshot_for,
    materialize_branch_schema,
    save_branch_snapshot,
)

__all__ = [
    "BranchRunner",
    "enter_branch",
    "get_branch_results",
    "leave_branch",
    "load_branch_snapshot",
    "load_branch_snapshot_for",
    "materialize_branch_schema",
    "merge_branch_results",
    "record_branch_result",
    "save_branch_snapshot",
]
