"""
Job abstraction — unit of work managed by the orchestration engine.

Execution semantics live in :class:`~palm.core.orchestration.execution.base_runner.JobRunner`
implementations; :class:`~palm.core.orchestration.engine.OrchestrationEngine` applies
lifecycle transitions. The job holds pluggable :class:`~palm.core.context.BaseState`.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any

from palm.core.context import BaseState
from palm.core.orchestration.exceptions import InvalidJobTransitionError
from palm.core.orchestration.job_state import JobState


class JobStatus(StrEnum):
    """Lifecycle states for an orchestrated job."""

    PENDING = "PENDING"
    RUNNING = "RUNNING"
    WAITING_FOR_INPUT = "WAITING_FOR_INPUT"
    SUCCEEDED = "SUCCEEDED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


@dataclass
class Job:
    """
    One unit of work submitted to ``OrchestrationEngine``.

    The ``executable`` field is opaque; runners interpret it (patterns, callables,
    descriptors, etc.).
    """

    id: str
    executable: Any
    state: BaseState = field(default_factory=JobState)
    metadata: dict[str, Any] = field(default_factory=dict)
    status: JobStatus = JobStatus.PENDING
    result: Any = None
    error: BaseException | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    started_at: datetime | None = None
    completed_at: datetime | None = None

    def __post_init__(self) -> None:
        if not self.id or not isinstance(self.id, str):
            raise ValueError("Job id must be a non-empty string")

    def _transition_to(
        self,
        new_status: JobStatus,
        *,
        result: Any = None,
        error: BaseException | None = None,
    ) -> None:
        """Apply a lifecycle transition (called by :class:`~palm.core.orchestration.engine.OrchestrationEngine` only)."""
        old = self.status
        if not self._is_valid_transition(old, new_status):
            raise InvalidJobTransitionError(self.id, str(old), str(new_status))

        now = datetime.now(UTC)
        if old == JobStatus.PENDING and new_status == JobStatus.RUNNING:
            self.started_at = now

        if new_status in (JobStatus.SUCCEEDED, JobStatus.FAILED, JobStatus.CANCELLED):
            self.completed_at = now
            if result is not None:
                self.result = result
            if error is not None:
                self.error = error

        self.status = new_status

    @staticmethod
    def _is_valid_transition(old: JobStatus, new: JobStatus) -> bool:
        if old == new:
            return True

        allowed: dict[JobStatus, set[JobStatus]] = {
            JobStatus.PENDING: {
                JobStatus.RUNNING,
                JobStatus.SUCCEEDED,
                JobStatus.FAILED,
                JobStatus.WAITING_FOR_INPUT,
                JobStatus.CANCELLED,
            },
            JobStatus.RUNNING: {
                JobStatus.SUCCEEDED,
                JobStatus.FAILED,
                JobStatus.WAITING_FOR_INPUT,
                JobStatus.CANCELLED,
                JobStatus.RUNNING,
            },
            JobStatus.WAITING_FOR_INPUT: {
                JobStatus.RUNNING,
                JobStatus.SUCCEEDED,
                JobStatus.FAILED,
                JobStatus.CANCELLED,
            },
            JobStatus.SUCCEEDED: set(),
            JobStatus.FAILED: set(),
            JobStatus.CANCELLED: set(),
        }
        return new in allowed.get(old, set())

    @property
    def is_terminal(self) -> bool:
        return self.status in (
            JobStatus.SUCCEEDED,
            JobStatus.FAILED,
            JobStatus.CANCELLED,
        )

    @property
    def is_live(self) -> bool:
        return self.status in (JobStatus.RUNNING, JobStatus.WAITING_FOR_INPUT)

    def snapshot(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "status": self.status.value,
            "metadata": dict(self.metadata),
            "result": self.result,
            "error": str(self.error) if self.error else None,
            "created_at": self.created_at.isoformat(),
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "state_keys": self.state.keys(),
        }

    def __repr__(self) -> str:
        return (
            f"Job(id={self.id!r}, status={self.status.value}, "
            f"live={self.is_live}, terminal={self.is_terminal})"
        )
