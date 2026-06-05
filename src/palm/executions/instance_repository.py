"""
Instance repository — durable ``ProcessInstance`` storage via ``StorageEngine``.
"""

from __future__ import annotations

from typing import Any
from uuid import uuid4

from palm.core.exceptions import StorageNotConfiguredError
from palm.core.orchestration import Job
from palm.core.storage import StorageEngine
from palm.definitions.flow import FlowDefinition
from palm.executions.exceptions import InstanceNotFoundError
from palm.executions.instance_sync import build_instance_from_job, update_instance_from_job
from palm.instances import ProcessInstance

_DEFAULT_PREFIX = "palm:instances"


class InstanceRepository:
    """CRUD for persisted process instances."""

    def __init__(
        self,
        storage: StorageEngine | None = None,
        *,
        prefix: str = _DEFAULT_PREFIX,
    ) -> None:
        self._storage = storage
        self._prefix = prefix.rstrip(":")
        self._cache: dict[str, ProcessInstance] = {}

    def create(
        self,
        job: Job,
        *,
        flow: FlowDefinition,
        instance_id: str | None = None,
        process_id: str | None = None,
        process_name: str | None = None,
    ) -> ProcessInstance:
        """Create and persist an instance from a new job."""
        instance = build_instance_from_job(
            job,
            flow=flow,
            instance_id=instance_id,
            process_id=process_id,
            process_name=process_name,
        )
        instance.append_status(job.status.value, event="created", job_id=job.id)
        return self.save(instance)

    def update(self, job: Job, *, instance_id: str | None = None) -> ProcessInstance:
        """Update an existing instance from the current job snapshot."""
        iid = instance_id or str(job.metadata.get("instance_id") or job.id)
        instance = self.get(iid)
        update_instance_from_job(instance, job)
        return self.save(instance)

    def save(self, instance: ProcessInstance) -> ProcessInstance:
        """Persist instance to memory and storage."""
        self._cache[instance.instance_id] = instance
        storage = self._storage
        if storage is not None and storage.is_initialized:
            try:
                storage.set(self._key(instance.instance_id), instance.to_dict())
                self._update_index(instance.instance_id)
            except StorageNotConfiguredError:
                pass
        return instance

    def get(self, instance_id: str) -> ProcessInstance:
        cached = self._cache.get(instance_id)
        if cached is not None:
            return cached
        record = self._load(instance_id)
        if record is None:
            raise InstanceNotFoundError(instance_id)
        instance = ProcessInstance.from_dict(record)
        self._cache[instance_id] = instance
        return instance

    def delete(self, instance_id: str) -> bool:
        self._cache.pop(instance_id, None)
        storage = self._storage
        if storage is None or not storage.is_initialized:
            return False
        try:
            storage.delete(self._key(instance_id))
            self._remove_from_index(instance_id)
            return True
        except StorageNotConfiguredError:
            return False

    def list_instances(self) -> list[ProcessInstance]:
        ids = set(self._cache.keys())
        storage = self._storage
        if storage is not None and storage.is_initialized:
            try:
                indexed = storage.get(self._index_key())
                if isinstance(indexed, list):
                    ids.update(str(item) for item in indexed)
            except StorageNotConfiguredError:
                pass
        return [self.get(iid) for iid in sorted(ids)]

    def new_instance_id(self) -> str:
        return f"inst-{uuid4().hex[:12]}"

    def _key(self, instance_id: str) -> str:
        return f"{self._prefix}:{instance_id}"

    def _index_key(self) -> str:
        return f"{self._prefix}:index"

    def _load(self, instance_id: str) -> dict[str, Any] | None:
        storage = self._storage
        if storage is None or not storage.is_initialized:
            return None
        try:
            value = storage.get(self._key(instance_id))
        except StorageNotConfiguredError:
            return None
        return value if isinstance(value, dict) else None

    def _update_index(self, instance_id: str) -> None:
        storage = self._storage
        if storage is None or not storage.is_initialized:
            return
        key = self._index_key()
        current = storage.get(key)
        ids = list(current) if isinstance(current, list) else []
        if instance_id not in ids:
            ids.append(instance_id)
            storage.set(key, ids)

    def _remove_from_index(self, instance_id: str) -> None:
        storage = self._storage
        if storage is None or not storage.is_initialized:
            return
        try:
            key = self._index_key()
            current = storage.get(key)
            if not isinstance(current, list):
                return
            ids = [item for item in current if item != instance_id]
            storage.set(key, ids)
        except StorageNotConfiguredError:
            return