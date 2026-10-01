"""
StateSnapshotHook — optional point-in-time blackboard captures on status transitions.
"""

from __future__ import annotations

from collections.abc import Collection
from typing import TYPE_CHECKING

from palm.common.exceptions import InstanceNotFoundError
from palm.common.persistence.instance_sync import InstanceSyncHooks
from palm.core.exceptions import RegistryError
from palm.core.orchestration.hooks import JobHookAdapter
from palm.core.registry import Registry
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

    Runs after :class:`~palm.system.runtime.job_hooks.instance_persistence.InstancePersistenceHook`
    so the durable instance record exists. ``sync`` is the system ``instance_sync``
    table. A missing pattern name raises. Other snapshot failures are swallowed
    so job execution never depends on this middleware.
    """

    def __init__(
        self,
        instances: InstanceRepository | InstanceManager,
        *,
        sync: Registry[InstanceSyncHooks] | None = None,
        snapshot_on_status: Collection[str] | None = None,
        max_snapshots_per_instance: int = 10,
    ) -> None:
        self._instances = instances
        self._sync = sync
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
        except RegistryError:
            raise
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

        snapshot = StateSnapshot.now(job, sync=self._sync, event="status_snapshot")
        self._instances.append_state_snapshot(
            str(instance_id),
            snapshot,
            max_snapshots=self._max_snapshots,
        )
