"""
TestBackend — deterministic backend for orchestration unit tests.

Lives outside ``palm.core`` to preserve core purity.
"""

from __future__ import annotations

from typing import Any

from palm.core.orchestration.exceptions import JobExecutionError
from palm.core.orchestration.execution.base_backend import ExecutionBackend
from palm.core.orchestration.job import Job, JobStatus


class TestBackend(ExecutionBackend):
    """
    Synchronous test backend accepting dict descriptors or callables.

    Dict shape::

        {"steps": N, "final_status": "SUCCEEDED"|"WAITING_FOR_INPUT"|"FAILED",
         "result": ..., "inject_error": exc}
    """

    def advance(self, job: Job, *, max_steps: int | None = None) -> JobStatus:
        if job.is_terminal:
            return job.status

        steps = max_steps or 10_000
        if steps < 1:
            raise ValueError("max_steps must be >= 1")

        job._allow_mutation = True
        try:
            executable = job.executable

            if callable(executable) and not isinstance(executable, dict):
                try:
                    result_status = executable(job)
                    if isinstance(result_status, JobStatus):
                        job._transition_to(result_status)
                    return job.status
                except Exception as exc:
                    job._transition_to(JobStatus.FAILED, error=exc)
                    raise JobExecutionError(
                        job.id, "callable executable raised", original=exc
                    ) from exc

            if isinstance(executable, dict):
                return self._advance_descriptor(job, executable, steps)

            job._transition_to(JobStatus.SUCCEEDED, result=executable)
            return JobStatus.SUCCEEDED

        finally:
            job._allow_mutation = False

    def _advance_descriptor(self, job: Job, descriptor: dict[str, Any], steps: int) -> JobStatus:
        total_steps = int(descriptor.get("steps", 1))
        target = descriptor.get("final_status", "SUCCEEDED")
        result = descriptor.get("result")
        inject_error = descriptor.get("inject_error")

        if job.status == JobStatus.WAITING_FOR_INPUT:
            if target in (JobStatus.SUCCEEDED.value, "SUCCEEDED"):
                job._transition_to(JobStatus.SUCCEEDED, result=result)
            elif target in (JobStatus.FAILED.value, "FAILED"):
                err = inject_error or RuntimeError("TestBackend forced failure on resume")
                job._transition_to(JobStatus.FAILED, error=err)
                raise JobExecutionError(job.id, "forced failure on resume", original=err) from err
            else:
                job._transition_to(JobStatus.SUCCEEDED, result=result)
            return job.status

        for _ in range(min(total_steps, steps)):
            if job.status != JobStatus.RUNNING:
                job._transition_to(JobStatus.RUNNING)

            if target == JobStatus.WAITING_FOR_INPUT.value:
                job._transition_to(JobStatus.WAITING_FOR_INPUT)
                return job.status

            if inject_error is not None:
                job._transition_to(JobStatus.FAILED, error=inject_error)
                raise JobExecutionError(
                    job.id, "injected by TestBackend", original=inject_error
                ) from inject_error

        if target in (JobStatus.SUCCEEDED.value, "SUCCEEDED"):
            job._transition_to(JobStatus.SUCCEEDED, result=result)
        elif target in (JobStatus.FAILED.value, "FAILED"):
            err = inject_error or RuntimeError("TestBackend forced failure")
            job._transition_to(JobStatus.FAILED, error=err)
            raise JobExecutionError(job.id, "forced by test descriptor", original=err) from err
        elif target in (JobStatus.WAITING_FOR_INPUT.value, "WAITING_FOR_INPUT"):
            job._transition_to(JobStatus.WAITING_FOR_INPUT)
        else:
            job._transition_to(JobStatus.SUCCEEDED, result=result)

        return job.status