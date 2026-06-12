"""
RunResult — outcome of a single job execution slice.

Runners produce ``RunResult``; :class:`~palm.core.orchestration.engine.OrchestrationEngine`
is the sole authority that applies it to :class:`~palm.core.orchestration.job.Job`.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from palm.core.orchestration.job import JobStatus


@dataclass(frozen=True)
class RunResult:
    """Describes how a job should look after one runner invocation."""

    status: JobStatus
    result: Any = None
    error: BaseException | None = None
    propagate: bool = False
    """When ``True``, schedulers re-raise ``error`` after applying the transition."""
