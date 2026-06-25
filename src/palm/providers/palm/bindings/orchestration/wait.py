"""Local job wait helpers for compositional invocations."""

from __future__ import annotations

import time
from typing import Any

from palm.core.orchestration import Job, JobStatus
from palm.core.orchestration.drive import drive_job
from palm.core.resource.invocation import WaitMode
from palm.providers.palm.exceptions import PalmTimeoutError


def wait_for_job(
    runtime: Any,
    job_id: str,
    timeout: float,
    wait_mode: WaitMode,
) -> Job:
    """Poll a local job until the configured wait policy is satisfied."""
    deadline = time.monotonic() + timeout
    last: Job | None = None
    while time.monotonic() < deadline:
        job = runtime.get_job(job_id)
        last = job
        if job_ready(job, wait_mode):
            return job
        if job.status == JobStatus.PENDING:
            _drive_pending_job_slice(runtime, job)
        runtime.wait_until_idle(timeout=min(0.1, max(0.0, deadline - time.monotonic())))
        time.sleep(0.01)
    raise PalmTimeoutError(format_wait_timeout(job_id, last, wait_mode, timeout))


def _drive_pending_job_slice(runtime: Any, job: Job) -> None:
    """
    Advance a pending child job inline while the parent blocks in ``wait_for_job``.

    Without this, :class:`~palm.common.runtimes.schedulers.queued.QueuedScheduler`
    deadlocks: the worker thread driving the parent cannot dequeue the child until
    the parent slice finishes, but the parent slice waits for the child.
    """
    engine = getattr(runtime, "orchestration", None)
    if engine is None:
        return
    scheduler = getattr(engine, "scheduler", None)
    runner = getattr(scheduler, "runner", None)
    if runner is None:
        return
    drive_job(engine, runner, job)


def job_ready(job: Job, wait_mode: WaitMode) -> bool:
    """Return whether ``job`` satisfies the configured wait policy."""
    if wait_mode == WaitMode.FIRE_AND_FORGET:
        return True
    if wait_mode == WaitMode.UNTIL_INPUT:
        return job.is_terminal or job.status == JobStatus.WAITING_FOR_INPUT
    return job.is_terminal


def format_wait_timeout(
    job_id: str,
    job: Job | None,
    wait_mode: WaitMode,
    timeout: float,
) -> str:
    """Build a human-readable timeout message for local job waits."""
    status = job.status.value if job is not None else "unknown"
    base = (
        f"Timed out after {timeout:g}s waiting for job {job_id!r} "
        f"(wait_mode={wait_mode.value}, current status={status})"
    )
    if (
        wait_mode == WaitMode.UNTIL_TERMINAL
        and job is not None
        and job.status == JobStatus.WAITING_FOR_INPUT
    ):
        return (
            f"{base}. The child flow is waiting for interactive input. "
            "Use wait_mode='until_input' on the resource step to return control "
            "to the parent wizard with the child job_id and instance_id."
        )
    if wait_mode == WaitMode.UNTIL_INPUT and job is not None and job.status == JobStatus.RUNNING:
        return (
            f"{base}. The child job has not reached WAITING_FOR_INPUT yet; "
            "increase timeout_seconds or verify the child flow exposes an interactive step."
        )
    if job is not None and job.status == JobStatus.PENDING:
        return (
            f"{base}. The child job was submitted but never started — "
            "this often indicates a queued-scheduler deadlock during nested compositional invokes."
        )
    return base