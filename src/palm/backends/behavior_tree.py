"""
BehaviorTreeBackend — runs ``BasePattern`` executables against job state.
"""

from __future__ import annotations

from palm.core.behavior_tree import BasePattern, PatternStatus
from palm.core.orchestration.exceptions import JobExecutionError
from palm.core.orchestration.execution.base_backend import ExecutionBackend
from palm.core.orchestration.job import Job, JobStatus


class BehaviorTreeBackend(ExecutionBackend):
    """Advances a ``BasePattern`` stored in ``job.executable`` using ``job.state``."""

    def advance(self, job: Job, *, max_steps: int | None = None) -> JobStatus:
        pattern = job.executable
        if not isinstance(pattern, BasePattern):
            raise JobExecutionError(
                job.id,
                "BehaviorTreeBackend requires a BasePattern executable",
            )

        ticks = max_steps if max_steps is not None else 10_000
        if ticks < 1:
            raise ValueError("max_steps must be >= 1")

        job._allow_mutation = True
        try:
            if job.status == JobStatus.PENDING:
                job._transition_to(JobStatus.RUNNING)

            for _ in range(ticks):
                try:
                    status = pattern.tick(job.state)
                except Exception as exc:
                    job._transition_to(JobStatus.FAILED, error=exc)
                    raise JobExecutionError(job.id, "pattern tick failed", original=exc) from exc

                if status == PatternStatus.WAITING_FOR_INPUT:
                    job._transition_to(JobStatus.WAITING_FOR_INPUT)
                    return job.status

                if status == PatternStatus.SUCCESS:
                    job._transition_to(
                        JobStatus.SUCCEEDED,
                        result=job.state.get("__result__"),
                    )
                    return job.status

                if status == PatternStatus.FAILURE:
                    job._transition_to(
                        JobStatus.FAILED,
                        error=job.state.get("__error__"),
                    )
                    return job.status

            if job.status == JobStatus.RUNNING:
                return job.status

            job._transition_to(
                JobStatus.FAILED,
                error=RuntimeError("pattern did not reach a terminal status"),
            )
            return job.status

        finally:
            job._allow_mutation = False
