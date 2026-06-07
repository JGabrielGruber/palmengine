"""
JobHook — middleware extension points for orchestration.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol, runtime_checkable

if TYPE_CHECKING:
    from palm.core.orchestration.engine import OrchestrationEngine
    from palm.core.orchestration.job import Job
    from palm.core.orchestration.run_result import RunResult


@runtime_checkable
class JobHook(Protocol):
    """Observe and extend job lifecycle without ad-hoc event wiring."""

    def on_job_submitted(self, engine: OrchestrationEngine, job: Job) -> None:
        """Called after a job is registered and the scheduler has driven it."""

    def on_job_status_changed(
        self,
        engine: OrchestrationEngine,
        job: Job,
        result: RunResult | None = None,
    ) -> None:
        """Called after :meth:`~palm.core.orchestration.engine.OrchestrationEngine.apply_result`."""


class JobHookAdapter:
    """No-op defaults for optional hook methods."""

    def on_job_submitted(self, engine: OrchestrationEngine, job: Job) -> None:
        return None

    def on_job_status_changed(
        self,
        engine: OrchestrationEngine,
        job: Job,
        result: RunResult | None = None,
    ) -> None:
        return None