"""
TestBackend — the primary (and only allowed) concrete ExecutionBackend inside
`palm/core/orchestration`.

This implementation is 100% deterministic, synchronous, and has zero external
dependencies (no threads, no I/O, no Behavior Tree, no domain code). It is the
foundation for all contract tests, edge-case tests, and fast developer feedback
in the Orchestration Engine.

It accepts simple declarative work descriptors or callables for maximum
flexibility in tests.

See `palm/core/orchestration/execution/backend.py` for the abstract contract.
"""

from __future__ import annotations

from ..exceptions import JobExecutionError
from ..job import Job, JobStatus


class TestBackend:
    """
    Primary backend for unit tests and the default used by `TestMode`.

    Accepts either:
    - A simple dict descriptor:
        {"steps": N, "final_status": "SUCCEEDED"|"WAITING_FOR_INPUT"|"FAILED",
         "result": ..., "inject_error": exc}
    - A callable(job: Job) -> JobStatus (full control for advanced tests)

    Characteristics:
    - 100% synchronous, no threads, no I/O, no real work.
    - Deterministic and extremely fast.
    - Perfect for the full Job state machine, WAITING flows, error isolation,
      shutdown-during-work, max-concurrency limits, etc.
    - Never imports or depends on the Behavior Tree engine or any domain code.
    """

    def advance(self, job: Job, *, max_steps: int | None = None) -> JobStatus:
        if job.is_terminal:
            return job.status

        steps = max_steps or 10_000
        if steps < 1:
            raise ValueError("max_steps must be >= 1")

        # Enable controlled mutation for this drive (orchestration internals only)
        job._allow_mutation = True

        try:
            executable = job.executable

            if callable(executable) and not isinstance(executable, dict):
                # Advanced usage: caller supplies full control callable
                try:
                    result_status = executable(job)
                    if isinstance(result_status, JobStatus):
                        job._transition_to(result_status)
                    return job.status
                except Exception as exc:
                    job._transition_to(JobStatus.FAILED, error=exc)
                    raise JobExecutionError(job.id, "callable executable raised", original=exc) from exc

            if isinstance(executable, dict):
                total_steps = int(executable.get("steps", 1))
                target = executable.get("final_status", "SUCCEEDED")
                result = executable.get("result")
                inject_error = executable.get("inject_error")

                # Resume path for a job previously put into WAITING
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

                # First submission / normal progress simulation
                for _ in range(min(total_steps, steps)):
                    if job.status != JobStatus.RUNNING:
                        job._transition_to(JobStatus.RUNNING)

                    if target == JobStatus.WAITING_FOR_INPUT.value:
                        job._transition_to(JobStatus.WAITING_FOR_INPUT)
                        return job.status

                    if inject_error is not None:
                        job._transition_to(JobStatus.FAILED, error=inject_error)
                        raise JobExecutionError(job.id, "injected by TestBackend", original=inject_error) from inject_error

                # Normal completion path
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

            # Fallback: treat anything else as instant success (useful for smoke tests)
            job._transition_to(JobStatus.SUCCEEDED, result=executable)
            return JobStatus.SUCCEEDED

        finally:
            job._allow_mutation = False
