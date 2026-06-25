"""
InstanceManager — cached, thread-safe coordination over InstanceRepository.
"""

from __future__ import annotations

import logging
import threading
from collections import OrderedDict
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

from palm.common.exceptions import InstanceActiveLimitError, InstanceNotFoundError
from palm.common.managers.base import BaseManager
from palm.common.persistence.instance_repository import InstanceRepository
from palm.core.orchestration import Job, JobStatus
from palm.definitions.flow import FlowDefinition
from palm.instances import ProcessInstance, StateSnapshot

if TYPE_CHECKING:
    from palm.app.settings import PalmSettings

logger = logging.getLogger(__name__)

_TERMINAL_STATUSES = frozenset(
    {
        JobStatus.SUCCEEDED.value,
        JobStatus.FAILED.value,
        JobStatus.CANCELLED.value,
    }
)
_STALE_ON_STARTUP = frozenset({JobStatus.RUNNING.value})


@dataclass(frozen=True)
class InstanceSummary:
    """Lightweight listing view without loading full instance payloads."""

    instance_id: str
    job_id: str
    status: str
    flow_name: str | None
    process_name: str | None
    current_step_slug: str | None
    updated_at: str
    snapshot_count: int = 0

    @classmethod
    def from_record(cls, record: dict[str, Any]) -> InstanceSummary:
        snapshots = record.get("state_snapshots")
        count = len(snapshots) if isinstance(snapshots, list) else 0
        return cls(
            instance_id=str(record.get("instance_id", "")),
            job_id=str(record.get("job_id", "")),
            status=str(record.get("status", "")),
            flow_name=record.get("flow_name"),
            process_name=record.get("process_name"),
            current_step_slug=record.get("current_step_slug") or record.get("wizard_step_slug"),
            updated_at=str(record.get("updated_at", "")),
            snapshot_count=count,
        )


@dataclass
class ReconciliationReport:
    """Outcome of startup instance reconciliation."""

    stale_marked: list[str] = field(default_factory=list)
    orphans_removed: list[str] = field(default_factory=list)

    @property
    def changed(self) -> bool:
        return bool(self.stale_marked or self.orphans_removed)


class InstanceManager(BaseManager):
    """
    Single coordination point for process instance lifecycle across runtimes.

    Adds LRU caching, active-instance tracking, lightweight summaries, and
    startup reconciliation on top of :class:`~palm.common.persistence.instance_repository.InstanceRepository`.
    """

    def __init__(
        self,
        repository: InstanceRepository,
        *,
        settings: PalmSettings | None = None,
    ) -> None:
        self._repository = repository
        self._settings = settings
        self._lock = threading.RLock()
        self._cache: OrderedDict[str, ProcessInstance] = OrderedDict()
        self._active: set[str] = set()
        self._initialized = False
        self._max_loaded = 128
        self._max_active = 32
        self._max_snapshots = 10
        self._reconcile_on_startup = True

    @property
    def repository(self) -> InstanceRepository:
        return self._repository

    @property
    def is_initialized(self) -> bool:
        return self._initialized

    @property
    def active_instance_ids(self) -> frozenset[str]:
        with self._lock:
            return frozenset(self._active)

    def initialize(self, **options: Any) -> None:
        if self._initialized:
            return

        settings = options.pop("settings", None) or self._settings
        if settings is not None:
            self._max_loaded = max(
                1, int(getattr(settings, "max_loaded_instances", self._max_loaded))
            )
            self._max_active = max(
                1, int(getattr(settings, "max_concurrent_active", self._max_active))
            )
            self._max_snapshots = max(
                1, int(getattr(settings, "max_snapshots_per_instance", self._max_snapshots))
            )
            self._reconcile_on_startup = bool(
                getattr(settings, "reconcile_instances_on_startup", self._reconcile_on_startup)
            )

        if "max_loaded_instances" in options:
            value = options.pop("max_loaded_instances")
            if value is not None:
                self._max_loaded = max(1, int(value))
        if "max_concurrent_active" in options:
            value = options.pop("max_concurrent_active")
            if value is not None:
                self._max_active = max(1, int(value))
        if "max_snapshots_per_instance" in options:
            value = options.pop("max_snapshots_per_instance")
            if value is not None:
                self._max_snapshots = max(1, int(value))
        if "reconcile_on_startup" in options:
            value = options.pop("reconcile_on_startup")
            if value is not None:
                self._reconcile_on_startup = bool(value)

        if self._reconcile_on_startup:
            self.reconcile()

        self._initialized = True

    def shutdown(self) -> None:
        if not self._initialized:
            return
        with self._lock:
            self._cache.clear()
            self._active.clear()
        self._initialized = False

    def reconcile(self) -> ReconciliationReport:
        """Mark stale running instances and purge orphan index entries."""
        report = ReconciliationReport()
        for instance_id in self._repository.list_instance_ids():
            record = self._repository.load_record(instance_id)
            if record is None:
                if self._repository.purge_index_entry(instance_id):
                    report.orphans_removed.append(instance_id)
                    logger.warning("Removed orphan instance index entry %r", instance_id)
                continue

            status = str(record.get("status", ""))
            if status not in _STALE_ON_STARTUP:
                continue

            try:
                instance = ProcessInstance.from_dict(record)
            except Exception:
                if self._repository.purge_index_entry(instance_id):
                    report.orphans_removed.append(instance_id)
                continue

            instance.append_status(
                JobStatus.WAITING_FOR_INPUT.value,
                event="reconciled_stale",
                previous_status=status,
            )
            self._repository.save(instance)
            self._cache_put(instance)
            report.stale_marked.append(instance_id)
            logger.info(
                "Reconciled stale instance %r (%s → WAITING_FOR_INPUT)",
                instance_id,
                status,
            )

        return report

    def mark_active(self, instance_id: str) -> None:
        with self._lock:
            if instance_id in self._active:
                return
            if len(self._active) >= self._max_active:
                raise InstanceActiveLimitError(
                    f"Active instance limit reached ({self._max_active})"
                )
            self._active.add(instance_id)

    def release_active(self, instance_id: str) -> None:
        with self._lock:
            self._active.discard(instance_id)

    def acquire(self, instance_id: str) -> ProcessInstance:
        """Load an instance and mark it active."""
        instance = self.get(instance_id)
        self.mark_active(instance_id)
        return instance

    def get(self, instance_id: str) -> ProcessInstance:
        with self._lock:
            cached = self._cache.get(instance_id)
            if cached is not None:
                self._cache.move_to_end(instance_id)
                return cached

        try:
            instance = self._repository.get(instance_id)
        except InstanceNotFoundError:
            raise

        with self._lock:
            self._cache_put(instance)
            return instance

    def create(
        self,
        job: Job,
        *,
        flow: FlowDefinition,
        instance_id: str | None = None,
        process_id: str | None = None,
        process_name: str | None = None,
    ) -> ProcessInstance:
        instance = self._repository.create(
            job,
            flow=flow,
            instance_id=instance_id,
            process_id=process_id,
            process_name=process_name,
        )
        with self._lock:
            self._cache_put(instance)
            self.mark_active(instance.instance_id)
        return instance

    def update(self, job: Job, *, instance_id: str | None = None) -> ProcessInstance:
        instance = self._repository.update(job, instance_id=instance_id)
        with self._lock:
            self._cache_put(instance)
            iid = instance.instance_id
            if instance.status in _TERMINAL_STATUSES:
                self._active.discard(iid)
            elif iid not in self._active:
                try:
                    self.mark_active(iid)
                except InstanceActiveLimitError:
                    pass
        return instance

    def save(self, instance: ProcessInstance) -> ProcessInstance:
        saved = self._repository.save(instance)
        with self._lock:
            self._cache_put(saved)
        return saved

    def delete(self, instance_id: str) -> bool:
        removed = self._repository.delete(instance_id)
        with self._lock:
            self._cache.pop(instance_id, None)
            self._active.discard(instance_id)
        return removed

    def list_summaries(self) -> list[InstanceSummary]:
        summaries: list[InstanceSummary] = []
        for instance_id in self._repository.list_instance_ids():
            record = self._repository.load_record(instance_id)
            if not isinstance(record, dict) or not record.get("instance_id"):
                continue
            try:
                summaries.append(InstanceSummary.from_record(record))
            except Exception:
                logger.warning("Skipping corrupt instance summary for %r", instance_id)
        return sorted(summaries, key=lambda item: item.updated_at, reverse=True)

    def list_instances(self) -> list[ProcessInstance]:
        instances: list[ProcessInstance] = []
        for instance_id in self._repository.list_instance_ids():
            try:
                instances.append(self.get(instance_id))
            except InstanceNotFoundError:
                continue
        return sorted(instances, key=lambda item: item.updated_at, reverse=True)

    def list_state_snapshots(self, instance_id: str) -> list[StateSnapshot]:
        return list(self.get(instance_id).state_snapshots)

    def append_state_snapshot(
        self,
        instance_id: str,
        snapshot: StateSnapshot,
        *,
        max_snapshots: int | None = None,
    ) -> ProcessInstance:
        limit = self._max_snapshots if max_snapshots is None else max_snapshots
        instance = self._repository.append_state_snapshot(
            instance_id,
            snapshot,
            max_snapshots=limit,
        )
        with self._lock:
            self._cache_put(instance)
        return instance

    def new_instance_id(self) -> str:
        return self._repository.new_instance_id()

    def _cache_put(self, instance: ProcessInstance) -> None:
        self._cache[instance.instance_id] = instance
        self._cache.move_to_end(instance.instance_id)
        self._evict_cache()

    def _evict_cache(self) -> None:
        while len(self._cache) > self._max_loaded:
            evicted = False
            for instance_id in list(self._cache.keys()):
                if instance_id in self._active:
                    continue
                del self._cache[instance_id]
                evicted = True
                break
            if not evicted:
                break
