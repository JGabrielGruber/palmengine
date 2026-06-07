"""
ExecutionContext — per-job view passed to runners and schedulers.
"""

from __future__ import annotations

from dataclasses import dataclass

from palm.core.orchestration.job import Job


@dataclass(frozen=True)
class ExecutionContext:
    """Immutable handle for one execution slice of a job."""

    job: Job