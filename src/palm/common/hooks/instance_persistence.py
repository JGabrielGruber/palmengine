"""
Execution-layer hooks — cross-cutting concerns for orchestration jobs.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from palm.common.exceptions import InstanceNotFoundError
from palm.core.orchestration.hooks import JobHookAdapter
from palm.definitions.flow import FlowDefinition

if TYPE_CHECKING:
    from palm.common.managers.instance_manager import InstanceManager
    from palm.common.persistence.instance_repository import InstanceRepository
    from palm.core.orchestration.engine import OrchestrationEngine
    from palm.core.orchestration.job import Job
    from palm.core.orchestration.run_result import RunResult


class InstancePersistenceHook(JobHookAdapter):
    """
    Track and persist jobs that carry an ``instance_id`` in metadata.

    Creates the instance record on first submit, then updates on status changes.
    """

    def __init__(self, instances: InstanceRepository | InstanceManager) -> None:
        self._instances = instances

    def on_job_submitted(self, engine: OrchestrationEngine, job: Job) -> None:
        self._ensure_instance(job)

    def on_job_status_changed(
        self,
        engine: OrchestrationEngine,
        job: Job,
        result: RunResult | None = None,
    ) -> None:
        self._ensure_instance(job)

    def _ensure_instance(self, job: Job) -> None:
        iid = job.metadata.get("instance_id")
        if not iid:
            return
        try:
            self._instances.get(str(iid))
            self._instances.update(job, instance_id=str(iid))
        except InstanceNotFoundError:
            flow_def = job.metadata.get("flow_definition")
            if not isinstance(flow_def, dict):
                return
            try:
                flow = FlowDefinition.from_dict(flow_def)
            except Exception:
                return
            try:
                self._instances.create(
                    job,
                    flow=flow,
                    instance_id=str(iid),
                    process_id=job.metadata.get("process_id"),
                    process_name=job.metadata.get("process"),
                )
            except Exception:
                return None
        except Exception:
            return None