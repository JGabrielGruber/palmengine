"""
StateSnapshotHook — optional point-in-time blackboard captures on status transitions.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Collection

from palm.common.exceptions import InstanceNotFoundError
from palm.core.orchestration.hooks import JobHookAdapter
from palm.instances.state_snapshot import StateSnapshot

if TYPE_CHECKING:
    from palm.common.managers.instance_manager import InstanceManager
    from palm.common.persistence.instance_repository import InstanceRepository
    from palm.core.orchestration.engine import OrchestrationEngine
    from palm.core.orchestration.job import Job
    from palm.core.orchestration.run_result import RunResult

_DEFAULT_STATUSES = frozenset({"WAITING_FOR_INPUT", "SUCCEEDED", "FAILED"})


class StateSnapshotHook(JobHookAdapter):
    """
    Capture blackboard state on configured job status transitions.

    Runs after :class:`~palm.common.hooks.instance_persistence.InstancePersistenceHook`
    so the durable instance record exists. Snapshot failures are swallowed so job
    execution never depends on this middleware.
    """

    def __init__(
        self,
        instances: InstanceRepository | InstanceManager,
        *,
        snapshot_on_status: Collection[str] | None = None,
        max_snapshots_per_instance: int = 10,
    ) -> None:
        self._instances = instances
        self._snapshot_on_status = frozenset(snapshot_on_status or _DEFAULT_STATUSES)
        self._max_snapshots = max(1, max_snapshots_per_instance)

    def on_job_status_changed(
        self,
        engine: OrchestrationEngine,
        job: Job,
        result: RunResult | None = None,
    ) -> None:
        try:
            self._maybe_snapshot(job)
        except Exception:
            return None

    def _maybe_snapshot(self, job: Job) -> None:
        if job.status.value not in self._snapshot_on_status:
            return

        instance_id = job.metadata.get("instance_id")
        if not instance_id:
            return

        try:
            self._instances.get(str(instance_id))
        except InstanceNotFoundError:
            return

        snapshot = StateSnapshot.now(job, event="status_snapshot")
        self._instances.append_state_snapshot(
            str(instance_id),
            snapshot,
            max_snapshots=self._max_snapshots,
        )