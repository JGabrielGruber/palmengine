"""
Orchestrator — the central coordinator of the Palm Orchestration Engine.

It owns the job registry, an EventBus (from palm.core.events), and an
OrchestrationMode (Strategy) that decides *how* work actually executes.

The Orchestrator itself is deliberately free of threads, loops, and
execution details — all of that lives in the current mode and its backends.

This module is part of Palm's general-purpose Orchestration Engine and must
remain completely independent of any wizard, UI, persistence, or domain concerns.
"""

from __future__ import annotations

import uuid
from typing import Any

from palm.core.events import EventBus

from .exceptions import JobNotFoundError, OrchestratorError
from .job import Job, JobStatus
from .mode.base import OrchestrationMode
from .mode.test_mode import TestMode  # sensible default


class Orchestrator:
    """
    High-level coordinator for managing and executing Jobs.

    Typical usage (especially in tests with TestMode):

        mode = TestMode()
        orch = Orchestrator(mode=mode)
        orch.start()

        job = orch.submit({"steps": 2, "final_status": "SUCCEEDED", "result": "done"})
        assert job.status == JobStatus.SUCCEEDED

        orch.shutdown()

    The same Orchestrator API works with any OrchestrationMode (future
    EmbeddedMode, ProcessMode, etc.).
    """

    def __init__(
        self,
        *,
        mode: OrchestrationMode | None = None,
        event_bus: EventBus | None = None,
        max_concurrent_jobs: int = 128,
    ) -> None:
        self._mode: OrchestrationMode = mode or TestMode()
        self.event_bus: EventBus = event_bus or EventBus()
        self.max_concurrent_jobs: int = max_concurrent_jobs

        self._jobs: dict[str, Job] = {}
        self._running = False

    # ------------------------------------------------------------------
    # Lifecycle (delegated to mode)
    # ------------------------------------------------------------------

    def start(self) -> None:
        if self._running:
            return
        self._mode.start()
        self._running = True
        self._publish("orchestrator.started", {})

    def shutdown(self, *, timeout: float = 5.0) -> None:
        if not self._running:
            return

        # Ask mode to stop its workers / loops first
        self._mode.shutdown(timeout=timeout)

        # Best-effort: cancel any still-live jobs
        for job in list(self._jobs.values()):
            if job.is_live:
                try:
                    self._mode.cancel_job(self, job)
                    self._publish("job.cancelled", {"job_id": job.id})
                except Exception:
                    pass  # defensive

        self._mode.on_orchestrator_shutdown(self)
        self._running = False
        self._publish("orchestrator.shutdown", {"jobs_remaining": len(self._jobs)})

    def is_running(self) -> bool:
        return self._running and self._mode.is_running()

    # ------------------------------------------------------------------
    # Job management (public API)
    # ------------------------------------------------------------------

    def submit(
        self,
        executable: Any,
        *,
        job_id: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> Job:
        """
        Create and register a new Job, then hand it to the current mode for execution.

        The executable is opaque — the active mode + its ExecutionBackend decide
        what to do with it (TestBackend descriptors, BehaviorTree instances via external backends, etc.).
        """
        if not self.is_running():
            self.start()

        if len(self._jobs) >= self.max_concurrent_jobs:
            raise OrchestratorError(
                f"Maximum concurrent jobs ({self.max_concurrent_jobs}) reached",
                code="MAX_JOBS_EXCEEDED",
            )

        jid = job_id or f"job-{uuid.uuid4().hex[:12]}"
        if jid in self._jobs:
            raise OrchestratorError(f"Job id already exists: {jid}", code="DUPLICATE_JOB_ID")

        job = Job(
            id=jid,
            executable=executable,
            metadata=dict(metadata or {}),
        )
        self._jobs[jid] = job

        self._publish("job.submitted", {"job_id": jid, "metadata": job.metadata})

        # Delegate to the strategy
        self._mode.submit_job(self, job)

        self._publish("job.status_changed", {"job_id": jid, "status": job.status.value})
        if job.is_terminal:
            self._publish("job.completed", {"job_id": jid, "status": job.status.value})

        return job

    def get_job(self, job_id: str) -> Job:
        if job_id not in self._jobs:
            raise JobNotFoundError(job_id)
        return self._jobs[job_id]

    def list_jobs(self, status: JobStatus | None = None) -> list[Job]:
        jobs = list(self._jobs.values())
        if status is not None:
            jobs = [j for j in jobs if j.status == status]
        return jobs

    def cancel_job(self, job_id: str) -> bool:
        job = self.get_job(job_id)
        if job.is_terminal:
            return False
        self._mode.cancel_job(self, job)
        self._publish("job.cancelled", {"job_id": job_id})
        return True

    def provide_input(self, job_id: str, key: str, value: Any) -> None:
        """
        Write a value into a waiting job's blackboard and notify the mode
        so it can resume execution (especially important for TestMode).
        """
        job = self.get_job(job_id)
        job.blackboard.set(key, value)
        self._publish("job.input_received", {"job_id": job_id, "key": key})

        if job.status == JobStatus.WAITING_FOR_INPUT:
            self._mode.resume_job(self, job)
            self._publish("job.status_changed", {"job_id": job_id, "status": job.status.value})
            if job.is_terminal:
                self._publish("job.completed", {"job_id": job_id, "status": job.status.value})

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _publish(self, name: str, payload: dict[str, Any]) -> None:
        self.event_bus.publish_named(name, payload)

    def __repr__(self) -> str:
        return (
            f"Orchestrator(mode={self._mode.name}, "
            f"running={self.is_running()}, jobs={len(self._jobs)})"
        )
