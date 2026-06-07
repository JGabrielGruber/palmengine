"""
Orchestration engine — job lifecycle and execution coordination.

Delegates execution to a :class:`~palm.core.orchestration.mode.base_mode.OrchestrationMode`
(job scheduler) and optional :class:`~palm.core.event.EventEngine` /
:class:`~palm.core.context.ContextEngine` for observability and scoped state.
"""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING, Any

from palm.core.base import BasePalmEngine
from palm.core.context import BaseState, ContextEngine
from palm.core.event import EventEngine
from palm.core.orchestration.events import OrchestrationEventType
from palm.core.orchestration.exceptions import (
    JobExecutionError,
    JobNotFoundError,
    OrchestratorError,
)
from palm.core.orchestration.execution_context import ExecutionContext
from palm.core.orchestration.hooks import JobHook
from palm.core.orchestration.input_capable import InputCapable, StepInspectable
from palm.core.orchestration.job import Job, JobStatus
from palm.core.orchestration.job_state import JobState
from palm.core.orchestration.mode.base_mode import OrchestrationMode
from palm.core.orchestration.mode.unconfigured_mode import UnconfiguredMode
from palm.core.orchestration.run_result import RunResult

if TYPE_CHECKING:
    pass


class OrchestrationEngine(BasePalmEngine):
    """
    Coordinates job registration, lifecycle, and mode-driven execution.

    Call :meth:`initialize` with an :class:`~palm.core.orchestration.mode.base_mode.OrchestrationMode`
    before submitting work (e.g. a runtime-specific mode or a test double).
    """

    def __init__(self) -> None:
        super().__init__(name="orchestration")
        self._mode: OrchestrationMode = UnconfiguredMode()
        self._event_engine: EventEngine | None = None
        self._context_engine: ContextEngine | None = None
        self._hooks: list[JobHook] = []
        self._jobs: dict[str, Job] = {}
        self._running = False
        self.max_concurrent_jobs = 128

    @property
    def mode(self) -> OrchestrationMode:
        return self._mode

    @property
    def scheduler(self) -> OrchestrationMode:
        """Preferred alias for :attr:`mode` (0.6+)."""
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
            # Waiting jobs are parked for input — not cancelled on shutdown.
            if job.status == JobStatus.RUNNING:
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
            raise OrchestratorError(f"Maximum concurrent jobs ({self.max_concurrent_jobs}) reached")

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
        self._notify_job_submitted(job)

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
        """Write input to job state by key (generic blackboard-style delivery)."""
        job = self.get_job(job_id)
        job.state.set(key, value)
        self._emit(
            OrchestrationEventType.JOB_INPUT_RECEIVED,
            {"job_id": job_id, "key": key},
        )

        if job.status == JobStatus.WAITING_FOR_INPUT:
            self.resume_job(job_id)

    def deliver_input(self, job_id: str, value: Any) -> str | None:
        """
        Deliver input through an :class:`~palm.core.orchestration.input_capable.InputCapable`
        executable (e.g. wizards) and resume when waiting.
        """
        job = self.get_job(job_id)
        executable = job.executable
        if not isinstance(executable, InputCapable):
            raise TypeError(f"Job {job_id!r} executable does not accept delivered input")

        slug = executable.provide_input(job.state, value)
        self._emit(
            OrchestrationEventType.JOB_INPUT_RECEIVED,
            {"job_id": job_id, "key": slug or "input", "value": value},
        )

        if job.status == JobStatus.WAITING_FOR_INPUT:
            self.resume_job(job_id)

        return slug

    def inspect_step(self, job_id: str) -> str | None:
        """Return the active step slug when the executable supports inspection."""
        job = self.get_job(job_id)
        executable = job.executable
        if not isinstance(executable, StepInspectable):
            raise TypeError(f"Job {job_id!r} executable does not expose step position")
        return executable.current_step_slug(job.state)

    def inspect_answers(self, job_id: str) -> dict[str, Any]:
        """Return collected answers when the executable supports inspection."""
        job = self.get_job(job_id)
        executable = job.executable
        if not isinstance(executable, StepInspectable):
            raise TypeError(f"Job {job_id!r} executable does not expose answers")
        return executable.answers(job.state)

    def resume_job(self, job_id: str) -> None:
        job = self.get_job(job_id)
        if job.status != JobStatus.WAITING_FOR_INPUT:
            return
        self._mode.resume_job(self, job)

    def execution_context(self, job: Job) -> ExecutionContext:
        """Build an :class:`~palm.core.orchestration.execution_context.ExecutionContext` for a job."""
        return ExecutionContext(job=job)

    def apply_result(self, job: Job, result: RunResult) -> None:
        """
        Apply a runner outcome — the single authority for job lifecycle transitions.

        Schedulers and runners must not mutate ``job.status`` directly; they produce
        a :class:`~palm.core.orchestration.run_result.RunResult` and delegate here.
        """
        if job.is_terminal and result.status != job.status:
            return

        if result.status != job.status:
            job._transition_to(result.status, result=result.result, error=result.error)
        else:
            if result.result is not None:
                job.result = result.result
            if result.error is not None:
                job.error = result.error

        self._publish_job_status(job)
        self._notify_job_status_changed(job, result)

        if result.propagate and result.error is not None:
            raise JobExecutionError(job.id, str(result.error), original=result.error)

    def _notify_job_submitted(self, job: Job) -> None:
        for hook in self._hooks:
            hook.on_job_submitted(self, job)

    def _notify_job_status_changed(self, job: Job, result: RunResult) -> None:
        for hook in self._hooks:
            hook.on_job_status_changed(self, job, result)

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
        scheduler = options.get("scheduler") or options.get("mode")
        if isinstance(scheduler, OrchestrationMode):
            self._mode = scheduler

        hooks = options.get("hooks")
        if hooks is not None:
            self._hooks = [hook for hook in hooks if isinstance(hook, JobHook)]

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
