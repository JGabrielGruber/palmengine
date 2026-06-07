"""
Instance resume helpers — status checks for process instance recovery.
"""

from __future__ import annotations

from palm.core.orchestration.job import JobStatus


def is_resumable_status(status: str) -> bool:
    """Return whether a persisted instance status can be resumed."""
    return status in (
        JobStatus.WAITING_FOR_INPUT.value,
        JobStatus.RUNNING.value,
        JobStatus.PENDING.value,
    )