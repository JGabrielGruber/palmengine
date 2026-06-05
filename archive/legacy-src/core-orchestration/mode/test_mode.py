"""
TestMode — the fully controllable, zero-side-effect OrchestrationMode for unit tests.

This is the **primary recommended mode** for all testing of the Orchestration
Engine (contract tests, edge/breaking scenarios, and integration with
specific backends).

Characteristics (by design):
- Everything runs synchronously in the caller's thread.
- No threads, no processes, no I/O, no blocking, no timers.
- Extremely fast and 100% deterministic.
- Exposes powerful test-only controls (force states, run_until_idle, etc.).
- Uses TestBackend by default (completely independent of Behavior Trees).

Never use TestMode in production code.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from ..job import JobStatus
from .base import OrchestrationMode

if TYPE_CHECKING:
    from ..engine import Orchestrator
    from ..execution.backend import ExecutionBackend
    from ..job import Job


class TestMode(OrchestrationMode):
    """
    Synchronous test double for OrchestrationMode.

    Typical usage in tests:

        mode = TestMode()
        orch = Orchestrator(mode=mode)
        job = orch.submit({"steps": 3, "final_status": "SUCCEEDED", "result": 99})
        assert job.status == JobStatus.SUCCEEDED
        assert job.result == 99

        # Waiting flow
        w = orch.submit({"steps": 1, "final_status": "WAITING_FOR_INPUT"})
        orch.provide_input(w.id, "answer", 42)
        assert w.status == JobStatus.SUCCEEDED

    Extra test-only methods are available directly on the mode instance when
    you need more control than the clean Orchestrator API provides.
    """

    def __init__(
        self,
        *,
        backend: ExecutionBackend | None = None,
        name: str = "TestMode",
    ) -> None:
        super().__init__(name=name)
        from ..execution.test_backend import (
            TestBackend,  # local import to avoid circularity at module load
        )

        self._backend: ExecutionBackend = backend or TestBackend()  # type: ignore[assignment]
        self._running = False

        # Test-only instrumentation
        self._force_next_status: dict[str, JobStatus] = {}
        self._step_counters: dict[str, int] = {}

    # ------------------------------------------------------------------
    # OrchestrationMode contract
    # ------------------------------------------------------------------

    def start(self) -> None:
        self._running = True

    def shutdown(self, *, timeout: float = 5.0) -> None:
        # TestMode has nothing to stop, but we honor the contract
        self._running = False
        # Best-effort: any remaining live jobs are left for the orchestrator
        # to mark CANCELLED after this returns.

    def is_running(self) -> bool:
        return self._running

    def submit_job(self, orchestrator: Orchestrator, job: Job) -> None:
        if not self._running:
            self.start()

        # Immediately drive using our backend (the whole point of TestMode)
        self._drive_job(job)

    def resume_job(self, orchestrator: Orchestrator, job: Job) -> None:
        if job.status == JobStatus.WAITING_FOR_INPUT:
            # Re-drive after input arrived
            self._drive_job(job)

    # ------------------------------------------------------------------
    # Powerful test-only controls (use sparingly; prefer Orchestrator API)
    # ------------------------------------------------------------------

    def run_until_idle(self, orchestrator: Orchestrator) -> None:
        """
        Keep driving any jobs that are still in RUNNING state until they all
        reach a non-RUNNING status (or hit internal guards).

        Extremely useful in tests that submit multiple pieces of work.
        """
        for job in list(orchestrator.list_jobs()):
            if job.status == JobStatus.RUNNING:
                self._drive_job(job)

    def force_job_status(self, job: Job, status: JobStatus) -> None:
        """
        Test escape hatch. Forcibly sets a job status, bypassing normal
        transition rules. This is intentionally powerful for testing
        edge/breaking scenarios.
        """
        job.status = status  # direct set for test power (bypasses machine)

    def simulate_step(self, job: Job) -> JobStatus:
        """Single-step advance using the backend (for fine-grained test control)."""
        job._allow_mutation = True
        try:
            return self._backend.advance(job, max_steps=1)
        finally:
            job._allow_mutation = False

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _drive_job(self, job: Job) -> None:
        """Drive the job with the backend until it stops being RUNNING."""
        job._allow_mutation = True
        try:
            # Apply any forced next status (test escape hatch)
            if job.id in self._force_next_status:
                forced = self._force_next_status.pop(job.id)
                job._transition_to(forced)
                return

            # Normal drive
            self._backend.advance(job, max_steps=10_000)
        finally:
            job._allow_mutation = False
