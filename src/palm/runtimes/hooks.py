"""
Runtime hooks — cross-cutting middleware for orchestration jobs.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from palm.core.auth import AuthEngine, Principal
from palm.core.orchestration.exceptions import JobAuthorizationError
from palm.core.orchestration.hooks import JobHookAdapter

if TYPE_CHECKING:
    from palm.core.orchestration.engine import OrchestrationEngine
    from palm.core.orchestration.job import Job
    from palm.core.orchestration.run_result import RunResult


@dataclass
class DriveSlice:
    """One scheduler drive cycle for a job."""

    job_id: str
    status: str
    started_at: float
    finished_at: float

    @property
    def duration_ms(self) -> float:
        return (self.finished_at - self.started_at) * 1000.0


@dataclass
class DriveObservabilityHook(JobHookAdapter):
    """
    Record per-job drive slices using drive-phase hook extension points.

    Suitable for metrics, tracing, and debugging without modifying runners or
    schedulers. Pass to :meth:`~palm.runtimes.base.BaseRuntime.start` via
    ``hooks=[...]`` or enable with ``observability=True``.
    """

    slices: list[DriveSlice] = field(default_factory=list)
    _pending: dict[str, float] = field(default_factory=dict, repr=False)

    def on_before_drive(self, engine: OrchestrationEngine, job: Job) -> None:
        self._pending[job.id] = time.monotonic()

    def on_after_drive(
        self,
        engine: OrchestrationEngine,
        job: Job,
        result: RunResult,
    ) -> None:
        started = self._pending.pop(job.id, time.monotonic())
        finished = time.monotonic()
        self.slices.append(
            DriveSlice(
                job_id=job.id,
                status=job.status.value,
                started_at=started,
                finished_at=finished,
            )
        )

    def drive_count(self, job_id: str) -> int:
        """Return how many drive slices have been recorded for a job."""
        return sum(1 for slice_ in self.slices if slice_.job_id == job_id)


@dataclass
class AuthMiddleware(JobHookAdapter):
    """
    Stamp jobs with the active principal and optionally enforce drive authorization.

    Pair with :class:`~palm.core.auth.AuthEngine` on
    :class:`~palm.runtimes.base.BaseRuntime`. Enable via ``auth_enforce=True``
    on :meth:`~palm.runtimes.base.BaseRuntime.start`.
    """

    auth: AuthEngine
    required_roles: tuple[str, ...] = ("user",)
    enforce_drive: bool = True

    def on_job_submitted(self, engine: OrchestrationEngine, job: Job) -> None:
        self._stamp_principal(job)

    def on_before_drive(self, engine: OrchestrationEngine, job: Job) -> None:
        self._stamp_principal(job)
        if not self.enforce_drive:
            return
        principal = self.auth.principal
        if principal is None or not self.auth.authorize(*self.required_roles):
            raise JobAuthorizationError(job.id, principal_id=principal.id if principal else None)

    def _stamp_principal(self, job: Job) -> None:
        principal = self.auth.principal
        if principal is None:
            return
        job.metadata.setdefault("principal_id", principal.id)
        if principal.roles:
            job.metadata.setdefault("principal_roles", list(principal.roles))


def authenticate_runtime(
    auth: AuthEngine, credentials: dict[str, object] | Principal | None
) -> None:
    """Apply startup credentials to an auth engine."""
    if credentials is None:
        return
    if isinstance(credentials, Principal):
        auth.bind_principal(credentials)
        return
    if isinstance(credentials, dict):
        auth.authenticate({k: v for k, v in credentials.items()})
