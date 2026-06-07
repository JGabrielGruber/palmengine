"""
BehaviorTreeBackend — runs ``BasePattern`` executables against job state.
"""

from __future__ import annotations

from palm.core.behavior_tree import BasePattern, PatternStatus
from palm.core.orchestration.execution.base_runner import JobRunner
from palm.core.orchestration.execution_context import ExecutionContext
from palm.core.orchestration.job import JobStatus
from palm.core.orchestration.run_result import RunResult


class BehaviorTreeBackend(JobRunner):
    """Advances a ``BasePattern`` stored in ``job.executable`` using ``job.state``."""

    def run(self, ctx: ExecutionContext, *, budget: int | None = None) -> RunResult:
        job = ctx.job
        if job.is_terminal:
            return RunResult(status=job.status, result=job.result)

        pattern = job.executable
        if not isinstance(pattern, BasePattern):
            return RunResult(
                status=JobStatus.FAILED,
                error=TypeError("BehaviorTreeBackend requires a BasePattern executable"),
                propagate=True,
            )

        ticks = budget if budget is not None else 10_000
        if ticks < 1:
            raise ValueError("budget must be >= 1")

        logical_status = job.status
        if logical_status == JobStatus.PENDING:
            logical_status = JobStatus.RUNNING

        for _ in range(ticks):
            try:
                status = pattern.tick(job.state)
            except Exception as exc:
                return RunResult(status=JobStatus.FAILED, error=exc, propagate=True)

            if status == PatternStatus.WAITING_FOR_INPUT:
                return RunResult(status=JobStatus.WAITING_FOR_INPUT)

            if status == PatternStatus.SUCCESS:
                return RunResult(
                    status=JobStatus.SUCCEEDED,
                    result=job.state.get("__result__"),
                )

            if status == PatternStatus.FAILURE:
                err = job.state.get("__error__")
                return RunResult(
                    status=JobStatus.FAILED,
                    error=err if isinstance(err, BaseException) else RuntimeError("pattern failed"),
                )

            logical_status = JobStatus.RUNNING

        if logical_status == JobStatus.RUNNING:
            return RunResult(status=JobStatus.RUNNING)

        return RunResult(
            status=JobStatus.FAILED,
            error=RuntimeError("pattern did not reach a terminal status"),
        )