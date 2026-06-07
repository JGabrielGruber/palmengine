"""
Execution-layer hooks — cross-cutting concerns for orchestration jobs.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from palm.core.orchestration.hooks import JobHookAdapter

if TYPE_CHECKING:
    from palm.core.orchestration.engine import OrchestrationEngine
    from palm.core.orchestration.job import Job
    from palm.core.orchestration.run_result import RunResult
    from palm.executions.instance_repository import InstanceRepository


class InstancePersistenceHook(JobHookAdapter):
    """Persist jobs that carry an ``instance_id`` in metadata on status changes."""

    def __init__(self, instances: InstanceRepository) -> None:
        self._instances = instances

    def on_job_status_changed(
        self,
        engine: OrchestrationEngine,
        job: Job,
        result: RunResult | None = None,
    ) -> None:
        if not job.metadata.get("instance_id"):
            return
        try:
            self._instances.update(job)
        except Exception:
            return None