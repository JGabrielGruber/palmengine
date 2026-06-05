"""
Orchestration engine — job lifecycle and execution coordination.

Delegates execution to an ``OrchestrationMode`` and optional ``EventEngine`` /
``ContextEngine`` for observability and scoped state.
"""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING, Any

from palm.core.base import BasePalmEngine
from palm.core.context import BaseState, ContextEngine
from palm.core.event import EventEngine
from palm.core.orchestration.events import OrchestrationEventType
from palm.core.orchestration.exceptions import JobNotFoundError, OrchestratorError
from palm.core.orchestration.job import Job, JobStatus
from palm.core.orchestration.job_state import JobState
from palm.core.orchestration.mode.base_mode import OrchestrationMode
from palm.core.orchestration.mode.test_mode import TestMode

if TYPE_CHECKING:
    pass


class OrchestrationEngine(BasePalmEngine):
    """
    Coordinates job registration, lifecycle, and mode-driven execution.

    Typical test setup::

        engine = OrchestrationEngine()
        engine.initialize(mode=TestMode())
        engine.start()
        job = engine.submit({"steps": 1, "final_status": "SUCCEEDED"})
    """

    def __init__(self) -> None:
        super().__init__(name="orchestration")
        self._mode: OrchestrationMode = TestMode()
        self._event_engine: EventEngine | None = None
        self._context_engine: ContextEngine | None = None
        self._jobs: dict[str, Job] = {}
        self._running = False
        self.max_concurrent_jobs = 128

    @property
    def mode(self) -> OrchestrationMode:
        return self._mode

    @property
    def event_engine(self) -> EventEngine | None:
        return self._event_engine

    @property
    def context_engine(self) -> ContextEngine | None:
        return self._context_engine

    @property
    def jobs(self) -> dict[str, Job]:
        return dict(self._jobs)

    def start(self) -> None:
        if self._running:
            return
        self._mode.start()
        self._running = True
        self._emit(OrchestrationEventType.ENGINE_STARTED, {})

    def stop(self, *, timeout: float = 5.0) -> None:
        """Stop the orchestration runtime and best-effort cancel live jobs."""
        if not self._running:
            return

        self._mode.shutdown(timeout=timeout)

        for job in list(self._jobs.values()):
            if job.is_live:
                try:
                    self._mode.cancel_job(self, job)
                    self._emit(OrchestrationEventType.JOB_CANCELLED, {"job_id": job.id})
                except Exception:
                    pass

        self._mode.on_engine_shutdown(self)
        self._running = False
        self._emit(
            OrchestrationEventType.ENGINE_SHUTDOWN,
            {"jobs_remaining": len(self._jobs)},
        )

    def is_running(self) -> bool:
        return self._running and self._mode.is_running()

    def submit(
        self,
        executable: Any,
        *,
        job_id: str | None = None,
        state: BaseState | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> Job:
        if not self.is_running():
            self.start()

        if len(self._jobs) >= self.max_concurrent_jobs:
            raise OrchestratorError(
                f"Maximum concurrent jobs ({self.max_concurrent_jobs}) reached"
            )

        jid = job_id or f"job-{uuid.uuid4().hex[:12]}"
        if jid in self._jobs:
            raise OrchestratorError(f"Job id already exists: {jid}")

        job_state = state if state is not None else JobState()
        job = Job(
            id=jid,
            executable=executable,
            state=job_state,
            metadata=dict(metadata or {}),
        )
        self._jobs[jid] = job

        self._bind_job_context(job)
        self._emit(
            OrchestrationEventType.JOB_SUBMITTED,
            {"job_id": jid, "metadata": job.metadata},
        )

        self._mode.submit_job(self, job)
        self._publish_job_status(job)

        return job

    def get_job(self, job_id: str) -> Job:
        if job_id not in self._jobs:
            raise JobNotFoundError(job_id)
        return self._jobs[job_id]

    def list_jobs(self, status: JobStatus | None = None) -> list[Job]:
        jobs = list(self._jobs.values())
        if status is not None:
            jobs = [job for job in jobs if job.status == status]
        return jobs

    def cancel_job(self, job_id: str) -> bool:
        job = self.get_job(job_id)
        if job.is_terminal:
            return False
        self._mode.cancel_job(self, job)
        self._emit(OrchestrationEventType.JOB_CANCELLED, {"job_id": job_id})
        return True

    def provide_input(self, job_id: str, key: str, value: Any) -> None:
        job = self.get_job(job_id)
        job.state.set(key, value)
        self._emit(
            OrchestrationEventType.JOB_INPUT_RECEIVED,
            {"job_id": job_id, "key": key},
        )

        if job.status == JobStatus.WAITING_FOR_INPUT:
            self.resume_job(job_id)

    def resume_job(self, job_id: str) -> None:
        job = self.get_job(job_id)
        if job.status != JobStatus.WAITING_FOR_INPUT:
            return
        self._mode.resume_job(self, job)
        self._publish_job_status(job)

    def _bind_job_context(self, job: Job) -> None:
        ctx = self._context_engine
        if ctx is None or not ctx.is_initialized:
            return
        ctx.push(f"job:{job.id}", state=job.state, job_id=job.id)

    def _publish_job_status(self, job: Job) -> None:
        self._emit(
            OrchestrationEventType.JOB_STATUS_CHANGED,
            {"job_id": job.id, "status": job.status.value},
        )
        if job.is_terminal:
            self._emit(
                OrchestrationEventType.JOB_COMPLETED,
                {"job_id": job.id, "status": job.status.value},
            )

    def _emit(self, event_type: str, payload: dict[str, Any]) -> None:
        bus = self._event_engine
        if bus is None or not bus.is_initialized:
            return
        bus.emit(event_type, **payload)

    def _do_initialize(self, **options: Any) -> None:
        mode = options.get("mode")
        if isinstance(mode, OrchestrationMode):
            self._mode = mode

        event_engine = options.get("event_engine")
        if isinstance(event_engine, EventEngine):
            self._event_engine = event_engine

        context_engine = options.get("context_engine")
        if isinstance(context_engine, ContextEngine):
            self._context_engine = context_engine

        max_jobs = options.get("max_concurrent_jobs")
        if isinstance(max_jobs, int) and max_jobs > 0:
            self.max_concurrent_jobs = max_jobs

    def _do_shutdown(self) -> None:
        self.stop()
        self._jobs.clear()