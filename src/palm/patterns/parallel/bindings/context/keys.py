"""
Parallel pattern state key conventions.
"""

from __future__ import annotations


class ParallelKeys:
    """Well-known keys written into parent ``BaseState`` during parallel execution."""

    PREFIX = "__parallel__"
    ACTIVE_BRANCH = f"{PREFIX}.active_branch"
    BRANCH_RESULTS = f"{PREFIX}.branch_results"
    MERGED = f"{PREFIX}.merged"
    MERGE_COMPLETE = f"{PREFIX}.merge_complete"
    COMPLETED = f"{PREFIX}.completed"
    BRANCH_STATE = "__branch_state__"
