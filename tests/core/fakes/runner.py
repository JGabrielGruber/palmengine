"""
TestRunner — deterministic runner for orchestration unit tests.

Lives outside ``palm.core`` to preserve core purity.
"""

from __future__ import annotations

from typing import Any

from palm.core.orchestration.execution.base_runner import JobRunner
from palm.core.orchestration.execution_context import ExecutionContext
from palm.core.orchestration.job import Job, JobStatus
from palm.core.orchestration.run_result import RunResult


class TestRunner(JobRunner):
    """
    Synchronous test runner accepting dict descriptors or callables.

    Dict shape::

        {"steps": N, "final_status": "SUCCEEDED"|"WAITING_FOR_INPUT"|"FAILED",
         "result": ..., "inject_error": exc}
    """

    def run(self, ctx: ExecutionContext, *, budget: int | None = None) -> RunResult:
        job = ctx.job
        if job.is_terminal:
            return RunResult(status=job.status, result=job.result)

        steps = budget or 10_000
        if steps < 1:
            raise ValueError("budget must be >= 1")

        executable = job.executable

        if callable(executable) and not isinstance(executable, dict):
            try:
                outcome = executable(job)
            except Exception as exc:
                return RunResult(status=JobStatus.FAILED, error=exc, propagate=True)
            if isinstance(outcome, RunResult):
                return outcome
            if isinstance(outcome, JobStatus):
                return RunResult(status=outcome)
            return RunResult(status=job.status)

        if isinstance(executable, dict):
            return self._run_descriptor(job, executable, steps)

        return RunResult(status=JobStatus.SUCCEEDED, result=executable)

    def _run_descriptor(self, job: Job, descriptor: dict[str, Any], steps: int) -> RunResult:
        total_steps = int(descriptor.get("steps", 1))
        target = descriptor.get("final_status", "SUCCEEDED")
        result = descriptor.get("result")
        inject_error = descriptor.get("inject_error")

        if job.status == JobStatus.WAITING_FOR_INPUT:
            if target in (JobStatus.SUCCEEDED.value, "SUCCEEDED"):
                return RunResult(status=JobStatus.SUCCEEDED, result=result)
            if target in (JobStatus.FAILED.value, "FAILED"):
                err = inject_error or RuntimeError("TestRunner forced failure on resume")
                return RunResult(status=JobStatus.FAILED, error=err, propagate=True)
            return RunResult(status=JobStatus.SUCCEEDED, result=result)

        for _ in range(min(total_steps, steps)):
            if target == JobStatus.WAITING_FOR_INPUT.value:
                return RunResult(status=JobStatus.WAITING_FOR_INPUT)

            if inject_error is not None:
                return RunResult(status=JobStatus.FAILED, error=inject_error, propagate=True)

        if target in (JobStatus.SUCCEEDED.value, "SUCCEEDED"):
            return RunResult(status=JobStatus.SUCCEEDED, result=result)
        if target in (JobStatus.FAILED.value, "FAILED"):
            err = inject_error or RuntimeError("TestRunner forced failure")
            return RunResult(status=JobStatus.FAILED, error=err, propagate=True)
        if target in (JobStatus.WAITING_FOR_INPUT.value, "WAITING_FOR_INPUT"):
            return RunResult(status=JobStatus.WAITING_FOR_INPUT)

        return RunResult(status=JobStatus.SUCCEEDED, result=result)