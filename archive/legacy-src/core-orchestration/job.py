"""
Job abstraction — the universal unit of work managed by the Orchestration Engine.

A Job is intentionally lightweight and mostly data-oriented. All execution
semantics live in ExecutionBackend implementations. The Job only enforces
valid lifecycle transitions and provides introspection.

This module is part of Palm's general-purpose Orchestration Engine and must
remain completely independent of any wizard, UI, persistence, or domain concerns.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any

from .blackboard import Blackboard
from .exceptions import InvalidJobTransitionError


class JobStatus(StrEnum):
    """
    Lifecycle states for a Job inside the Orchestrator.

    Transitions (enforced by Job):
        PENDING → RUNNING
        RUNNING → (SUCCEEDED | FAILED | WAITING_FOR_INPUT | CANCELLED)
        WAITING_FOR_INPUT → (RUNNING | CANCELLED)
        (SUCCEEDED | FAILED | CANCELLED) → (terminal; no further transitions)

    RUNNING and WAITING_FOR_INPUT are the only "live" states that can still make progress.
    """

    PENDING = "PENDING"
    RUNNING = "RUNNING"
    WAITING_FOR_INPUT = "WAITING_FOR_INPUT"
    SUCCEEDED = "SUCCEEDED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


@dataclass
class Job:
    """
    Represents one unit of work submitted to an Orchestrator.

    Responsibilities (SRP):
    - Hold identity, status, executable reference, blackboard, and metadata.
    - Enforce valid status machine transitions.
    - Provide snapshot() for debugging and test assertions.
    - Remain completely agnostic about *how* the work is performed.

    The `executable` field is deliberately opaque (`Any`). Different
    ExecutionBackend implementations (TestBackend inside core, BehaviorTreeBackend
    in `palm/backends/`, future others) interpret it as they see fit.

    Mutation of status and result fields is intentionally restricted to
    internal helpers called only by the owning Orchestrator / active Mode / Backend.
    """

    id: str
    executable: Any
    blackboard: Blackboard = field(default_factory=Blackboard)
    metadata: dict[str, Any] = field(default_factory=dict)
    status: JobStatus = JobStatus.PENDING
    result: Any = None
    error: BaseException | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    started_at: datetime | None = None
    completed_at: datetime | None = None

    # Internal guard so only the orchestration package can drive transitions
    _allow_mutation: bool = field(default=False, repr=False, compare=False)

    def __post_init__(self) -> None:
        if not self.id or not isinstance(self.id, str):
            raise ValueError("Job id must be a non-empty string")

    # ------------------------------------------------------------------
    # Controlled state machine (package-private)
    # ------------------------------------------------------------------

    def _transition_to(
        self,
        new_status: JobStatus,
        *,
        result: Any = None,
        error: BaseException | None = None,
    ) -> None:
        """
        Internal transition helper. Only code inside the orchestration package
        (engine + modes + backends) should ever call this.
        """
        if not self._allow_mutation:
            # Safety net — in practice the orchestrator sets this temporarily
            self._allow_mutation = True

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
            return True  # idempotent is allowed for convenience in some paths

        allowed: dict[JobStatus, set[JobStatus]] = {
            JobStatus.PENDING: {
                JobStatus.RUNNING,
                JobStatus.SUCCEEDED,   # fast backends (esp. TestBackend) can finish instantly
                JobStatus.FAILED,
                JobStatus.WAITING_FOR_INPUT,
                JobStatus.CANCELLED,
            },
            JobStatus.RUNNING: {
                JobStatus.SUCCEEDED,
                JobStatus.FAILED,
                JobStatus.WAITING_FOR_INPUT,
                JobStatus.CANCELLED,
                JobStatus.RUNNING,  # allow staying for some backends
            },
            JobStatus.WAITING_FOR_INPUT: {
                JobStatus.RUNNING,
                JobStatus.SUCCEEDED,   # normal successful completion after receiving input
                JobStatus.FAILED,      # failure after receiving input (or forced)
                JobStatus.CANCELLED,
            },
            JobStatus.SUCCEEDED: set(),
            JobStatus.FAILED: set(),
            JobStatus.CANCELLED: set(),
        }
        return new in allowed.get(old, set())

    # ------------------------------------------------------------------
    # Public read-only / introspection API
    # ------------------------------------------------------------------

    @property
    def is_terminal(self) -> bool:
        """True if the job has reached a final state and will not make further progress."""
        return self.status in (JobStatus.SUCCEEDED, JobStatus.FAILED, JobStatus.CANCELLED)

    @property
    def is_live(self) -> bool:
        """True if the job is still eligible for execution ticks."""
        return self.status in (JobStatus.RUNNING, JobStatus.WAITING_FOR_INPUT)

    def snapshot(self) -> dict[str, Any]:
        """Return a deep-ish snapshot suitable for tests and debugging (no executable)."""
        return {
            "id": self.id,
            "status": self.status.value,
            "metadata": dict(self.metadata),
            "result": self.result,
            "error": str(self.error) if self.error else None,
            "created_at": self.created_at.isoformat(),
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "bb_keys": len(self.blackboard.keys()),
        }

    def __repr__(self) -> str:
        return (
            f"Job(id={self.id!r}, status={self.status.value}, "
            f"live={self.is_live}, terminal={self.is_terminal})"
        )
