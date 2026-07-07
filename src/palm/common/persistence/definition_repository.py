"""
Definition repository — in-memory registry with optional ``StorageEngine`` persistence.
"""

from __future__ import annotations

from typing import Any

from palm.common.exceptions import DefinitionNotFoundError
from palm.core.exceptions import StorageNotConfiguredError
from palm.core.storage import StorageEngine
from palm.definitions.flow import FlowDefinition
from palm.definitions.process import ProcessDefinition
from palm.definitions.resource import ResourceDefinition
from palm.definitions.schema import StateSchemaDefinition

_DEFAULT_PREFIX = "palm:definitions"


class DefinitionRepository:
    """
    CRUD for flow, process, resource, and state schema definitions.

    Code-defined definitions can be registered in memory. When a
    ``StorageEngine`` is attached and initialized, ``save_*`` persists records
    and ``get_*`` falls back to storage after the in-memory cache.
    """

    def __init__(
        self,
        storage: StorageEngine | None = None,
        *,
        prefix: str = _DEFAULT_PREFIX,
    ) -> None:
        self._storage = storage
        self._prefix = prefix.rstrip(":")
        self._flows_by_id: dict[str, FlowDefinition] = {}
        self._flows_by_name: dict[str, FlowDefinition] = {}
        self._flow_revisions: dict[str, dict[int, FlowDefinition]] = {}
        self._flow_latest_revision: dict[str, int] = {}
        self._processes_by_id: dict[str, ProcessDefinition] = {}
        self._processes_by_name: dict[str, ProcessDefinition] = {}
        self._schemas_by_id: dict[str, StateSchemaDefinition] = {}
        self._schemas_by_name: dict[str, StateSchemaDefinition] = {}
        self._resources_by_id: dict[str, ResourceDefinition] = {}
        self._resources_by_name: dict[str, ResourceDefinition] = {}

    @property
    def prefix(self) -> str:
        return self._prefix

    # ------------------------------------------------------------------
    # Flow CRUD
    # ------------------------------------------------------------------

    def register_flow(self, flow: FlowDefinition) -> FlowDefinition:
        """Publish a flow revision in memory (does not persist)."""
        return self._publish_flow_revision(flow, persist=False)

    def save_flow(self, flow: FlowDefinition) -> FlowDefinition:
        """Publish and persist a flow definition revision."""
        return self._publish_flow_revision(flow, persist=True)

    def publish_flow_revision(self, flow: FlowDefinition) -> FlowDefinition:
        """Append a new flow revision (persists when storage is configured)."""
        persist = self._storage is not None and self._storage.is_initialized
        return self._publish_flow_revision(flow, persist=persist)

    def get_latest_revision(self, flow_id: str) -> int | None:
        """Return the latest revision number for ``flow_id``, if any."""
        if flow_id in self._flow_latest_revision:
            return self._flow_latest_revision[flow_id]
        latest = self._load_latest_revision_number(flow_id)
        if latest is not None:
            self._flow_latest_revision[flow_id] = latest
        return latest

    def list_flow_revisions(self, flow_id: str) -> list[dict[str, int | str]]:
        """Return revision index rows for ``flow_id``."""
        self.get_flow_by_id(flow_id)
        numbers = self._revision_numbers(flow_id)
        return [{"flow_id": flow_id, "revision": revision} for revision in numbers]

    def get_flow(
        self,
        ref: str,
        *,
        by_id: bool = False,
        revision: int | None = None,
    ) -> FlowDefinition:
        """Load a flow by id (default) or by display name."""
        if by_id:
            return self.get_flow_by_id(ref, revision=revision)
        return self.get_flow_by_name(ref, revision=revision)

    def get_flow_by_id(
        self,
        definition_id: str,
        *,
        revision: int | None = None,
    ) -> FlowDefinition:
        if revision is not None:
            cached_revisions = self._flow_revisions.get(definition_id)
            if cached_revisions is not None:
                cached = cached_revisions.get(revision)
                if cached is not None:
                    return cached
            record = self._load_flow_revision_record(definition_id, revision)
            if record is None:
                raise DefinitionNotFoundError("flow", definition_id)
            flow = FlowDefinition.from_dict(record)
            self._cache_flow_revision(flow)
            return flow

        cached = self._flows_by_id.get(definition_id)
        if cached is not None:
            return cached

        latest = self._load_latest_revision_number(definition_id)
        if latest is not None:
            return self.get_flow_by_id(definition_id, revision=latest)

        record = self._load_record("flow", definition_id)
        if record is None:
            raise DefinitionNotFoundError("flow", definition_id)
        flow = FlowDefinition.from_dict(record)
        if flow.revision is None:
            flow = FlowDefinition(
                name=flow.name,
                pattern=flow.pattern,
                options=flow.options,
                id=flow.id,
                revision=1,
                state_schema_ref=flow.state_schema_ref,
                state_schema=flow.state_schema,
            )
        self._cache_flow_revision(flow)
        self._index_flow_latest(flow)
        return flow

    def get_flow_by_name(self, name: str, *, revision: int | None = None) -> FlowDefinition:
        cached = self._flows_by_name.get(name)
        if cached is not None and revision is None:
            return cached
        for flow in self._flows_by_id.values():
            if flow.name == name:
                if revision is None:
                    return flow
                return self.get_flow_by_id(flow.definition_id, revision=revision)
        loaded = self._scan_storage_for_name("flow", name)
        if isinstance(loaded, FlowDefinition):
            self._cache_flow_revision(loaded)
            self._index_flow_latest(loaded)
            if revision is None:
                return self.get_flow_by_id(loaded.definition_id)
            return self.get_flow_by_id(loaded.definition_id, revision=revision)
        raise DefinitionNotFoundError("flow", name)

    def delete_flow(self, ref: str, *, by_id: bool = True) -> bool:
        """Remove all revisions of a flow from memory and storage."""
        try:
            flow = self.get_flow(ref, by_id=by_id)
        except DefinitionNotFoundError:
            return False
        flow_id = flow.definition_id
        self._unindex_flow(flow)
        for revision in list(self._revision_numbers(flow_id)):
            self._delete_flow_revision_record(flow_id, revision)
        self._flow_revisions.pop(flow_id, None)
        self._flow_latest_revision.pop(flow_id, None)
        self._delete_record("flow", flow_id)
        self._delete_latest_revision_pointer(flow_id)
        return True

    def list_flows(self) -> list[FlowDefinition]:
        """Return all flows known in memory or storage indexes."""
        ids = self._collect_ids("flow", self._flows_by_id)
        flows: list[FlowDefinition] = []
        for definition_id in ids:
            try:
                flows.append(self.get_flow_by_id(definition_id))
            except DefinitionNotFoundError:
                continue
        return flows

    def has_flow(self, ref: str, *, by_id: bool = True) -> bool:
        try:
            self.get_flow(ref, by_id=by_id)
            return True
        except DefinitionNotFoundError:
            return False

    # ------------------------------------------------------------------
    # Process CRUD
    # ------------------------------------------------------------------

    def register_process(self, process: ProcessDefinition) -> ProcessDefinition:
        """Register a process in memory (does not persist)."""
        self._index_process(process)
        return process

    def save_process(self, process: ProcessDefinition) -> ProcessDefinition:
        """Register and persist a process definition."""
        self._index_process(process)
        storage = self._require_storage()
        storage.set(
            self._key("process", process.definition_id),
            process.to_storage_record(),
        )
        self._update_index("process", process.definition_id)
        return process

    def get_process(self, ref: str, *, by_id: bool = False) -> ProcessDefinition:
        if by_id:
            return self.get_process_by_id(ref)
        return self.get_process_by_name(ref)

    def get_process_by_id(self, definition_id: str) -> ProcessDefinition:
        cached = self._processes_by_id.get(definition_id)
        if cached is not None:
            return cached
        record = self._load_record("process", definition_id)
        if record is None:
            raise DefinitionNotFoundError("process", definition_id)
        process = ProcessDefinition.from_dict(record)
        self._index_process(process)
        return process

    def get_process_by_name(self, name: str) -> ProcessDefinition:
        cached = self._processes_by_name.get(name)
        if cached is not None:
            return cached
        for process in self._processes_by_id.values():
            if process.name == name:
                return process
        loaded = self._scan_storage_for_name("process", name)
        if isinstance(loaded, ProcessDefinition):
            self._index_process(loaded)
            return loaded
        raise DefinitionNotFoundError("process", name)

    def delete_process(self, ref: str, *, by_id: bool = True) -> bool:
        try:
            process = self.get_process(ref, by_id=by_id)
        except DefinitionNotFoundError:
            return False
        self._unindex_process(process)
        self._delete_record("process", process.definition_id)
        return True

    def list_processes(self) -> list[ProcessDefinition]:
        ids = self._collect_ids("process", self._processes_by_id)
        processes: list[ProcessDefinition] = []
        for definition_id in ids:
            try:
                processes.append(self.get_process_by_id(definition_id))
            except DefinitionNotFoundError:
                continue
        return processes

    def has_process(self, ref: str, *, by_id: bool = True) -> bool:
        try:
            self.get_process(ref, by_id=by_id)
            return True
        except DefinitionNotFoundError:
            return False

    # ------------------------------------------------------------------
    # State schema CRUD
    # ------------------------------------------------------------------

    def register_schema(self, schema: StateSchemaDefinition) -> StateSchemaDefinition:
        """Register a state schema in memory (does not persist)."""
        self._index_schema(schema)
        return schema

    def save_schema(self, schema: StateSchemaDefinition) -> StateSchemaDefinition:
        """Register and persist a state schema definition."""
        self._index_schema(schema)
        storage = self._require_storage()
        storage.set(
            self._key("state_schema", schema.definition_id),
            schema.to_storage_record(),
        )
        self._update_index("state_schema", schema.definition_id)
        return schema

    def get_schema(self, ref: str, *, by_id: bool = False) -> StateSchemaDefinition:
        """Load a state schema by id (default) or by display name."""
        if by_id:
            return self.get_schema_by_id(ref)
        return self.get_schema_by_name(ref)

    def get_schema_by_id(self, definition_id: str) -> StateSchemaDefinition:
        cached = self._schemas_by_id.get(definition_id)
        if cached is not None:
            return cached
        record = self._load_record("state_schema", definition_id)
        if record is None:
            raise DefinitionNotFoundError("state_schema", definition_id)
        schema = StateSchemaDefinition.from_dict(record)
        self._index_schema(schema)
        return schema

    def get_schema_by_name(self, name: str) -> StateSchemaDefinition:
        cached = self._schemas_by_name.get(name)
        if cached is not None:
            return cached
        for schema in self._schemas_by_id.values():
            if schema.name == name:
                return schema
        loaded = self._scan_storage_for_name("state_schema", name)
        if isinstance(loaded, StateSchemaDefinition):
            self._index_schema(loaded)
            return loaded
        raise DefinitionNotFoundError("state_schema", name)

    def delete_schema(self, ref: str, *, by_id: bool = True) -> bool:
        try:
            schema = self.get_schema(ref, by_id=by_id)
        except DefinitionNotFoundError:
            return False
        self._unindex_schema(schema)
        self._delete_record("state_schema", schema.definition_id)
        return True

    def list_schemas(self) -> list[StateSchemaDefinition]:
        ids = self._collect_ids("state_schema", self._schemas_by_id)
        schemas: list[StateSchemaDefinition] = []
        for definition_id in ids:
            try:
                schemas.append(self.get_schema_by_id(definition_id))
            except DefinitionNotFoundError:
                continue
        return schemas

    def has_schema(self, ref: str, *, by_id: bool = True) -> bool:
        try:
            self.get_schema(ref, by_id=by_id)
            return True
        except DefinitionNotFoundError:
            return False

    # ------------------------------------------------------------------
    # Resource CRUD
    # ------------------------------------------------------------------

    def register_resource(self, resource: ResourceDefinition) -> ResourceDefinition:
        """Register a resource in memory (does not persist)."""
        self._index_resource(resource)
        return resource

    def save_resource(self, resource: ResourceDefinition) -> ResourceDefinition:
        """Register and persist a resource definition."""
        self._index_resource(resource)
        storage = self._require_storage()
        storage.set(
            self._key("resource", resource.definition_id),
            resource.to_storage_record(),
        )
        self._update_index("resource", resource.definition_id)
        return resource

    def get_resource(self, ref: str, *, by_id: bool = False) -> ResourceDefinition:
        """Load a resource by id (default) or by display name."""
        if by_id:
            return self.get_resource_by_id(ref)
        return self.get_resource_by_name(ref)

    def get_resource_by_id(self, definition_id: str) -> ResourceDefinition:
        cached = self._resources_by_id.get(definition_id)
        if cached is not None:
            return cached
        record = self._load_record("resource", definition_id)
        if record is None:
            raise DefinitionNotFoundError("resource", definition_id)
        resource = ResourceDefinition.from_dict(record)
        self._index_resource(resource)
        return resource

    def get_resource_by_name(self, name: str) -> ResourceDefinition:
        cached = self._resources_by_name.get(name)
        if cached is not None:
            return cached
        for resource in self._resources_by_id.values():
            if resource.name == name:
                return resource
        loaded = self._scan_storage_for_name("resource", name)
        if isinstance(loaded, ResourceDefinition):
            self._index_resource(loaded)
            return loaded
        raise DefinitionNotFoundError("resource", name)

    def delete_resource(self, ref: str, *, by_id: bool = True) -> bool:
        try:
            resource = self.get_resource(ref, by_id=by_id)
        except DefinitionNotFoundError:
            return False
        self._unindex_resource(resource)
        self._delete_record("resource", resource.definition_id)
        return True

    def list_resources(self) -> list[ResourceDefinition]:
        ids = self._collect_ids("resource", self._resources_by_id)
        resources: list[ResourceDefinition] = []
        for definition_id in ids:
            try:
                resources.append(self.get_resource_by_id(definition_id))
            except DefinitionNotFoundError:
                continue
        return resources

    def list_resources_by_provider(self, provider: str) -> list[ResourceDefinition]:
        """Return resources registered for a given provider name."""
        return [item for item in self.list_resources() if item.provider == provider]

    def find_resources(self, query: str) -> list[ResourceDefinition]:
        """Case-insensitive search across resource name, id, provider, and action."""
        needle = query.strip().lower()
        if not needle:
            return self.list_resources()
        matches: list[ResourceDefinition] = []
        for resource in self.list_resources():
            haystack = " ".join(
                (
                    resource.name,
                    resource.definition_id,
                    resource.provider,
                    resource.action,
                    str(resource.resource_id or ""),
                ),
            ).lower()
            if needle in haystack:
                matches.append(resource)
        return matches

    def has_resource(self, ref: str, *, by_id: bool = True) -> bool:
        try:
            self.get_resource(ref, by_id=by_id)
            return True
        except DefinitionNotFoundError:
            return False

    # ------------------------------------------------------------------
    # Internal indexing / storage
    # ------------------------------------------------------------------

    def _publish_flow_revision(self, flow: FlowDefinition, *, persist: bool) -> FlowDefinition:
        flow_id = flow.definition_id
        next_revision = (self._flow_latest_revision.get(flow_id) or 0) + 1
        published = FlowDefinition(
            name=flow.name,
            pattern=flow.pattern,
            options=dict(flow.options),
            id=flow.id,
            revision=next_revision,
            state_schema_ref=flow.state_schema_ref,
            state_schema=dict(flow.state_schema) if flow.state_schema is not None else None,
        )
        self._cache_flow_revision(published)
        self._index_flow_latest(published)
        if persist:
            storage = self._require_storage()
            storage.set(
                self._flow_revision_key(flow_id, next_revision),
                published.to_storage_record(),
            )
            storage.set(self._flow_latest_key(flow_id), next_revision)
            self._append_revision_index(flow_id, next_revision)
            self._update_index("flow", flow_id)
        return published

    def _cache_flow_revision(self, flow: FlowDefinition) -> None:
        if flow.revision is None:
            return
        revisions = self._flow_revisions.setdefault(flow.definition_id, {})
        revisions[flow.revision] = flow
        self._flow_latest_revision[flow.definition_id] = max(
            self._flow_latest_revision.get(flow.definition_id, 0),
            flow.revision,
        )

    def _index_flow_latest(self, flow: FlowDefinition) -> None:
        self._flows_by_id[flow.definition_id] = flow
        self._flows_by_name[flow.name] = flow

    def _index_flow(self, flow: FlowDefinition) -> None:
        self._index_flow_latest(flow)

    def _unindex_flow(self, flow: FlowDefinition) -> None:
        self._flows_by_id.pop(flow.definition_id, None)
        if self._flows_by_name.get(flow.name) is flow:
            self._flows_by_name.pop(flow.name, None)

    def _revision_numbers(self, flow_id: str) -> list[int]:
        numbers = set(self._flow_revisions.get(flow_id, {}))
        storage = self._storage
        if storage is not None and storage.is_initialized:
            try:
                indexed = storage.get(self._flow_revisions_index_key(flow_id))
                if isinstance(indexed, list):
                    numbers.update(int(item) for item in indexed)
            except StorageNotConfiguredError:
                pass
        if not numbers:
            latest = self._flow_latest_revision.get(flow_id)
            if latest is not None:
                numbers.add(latest)
        return sorted(numbers)

    def _flow_revision_key(self, flow_id: str, revision: int) -> str:
        return f"{self._prefix}:flow:{flow_id}:rev:{revision}"

    def _flow_latest_key(self, flow_id: str) -> str:
        return f"{self._prefix}:flow:{flow_id}:latest"

    def _flow_revisions_index_key(self, flow_id: str) -> str:
        return f"{self._prefix}:flow:{flow_id}:revs"

    def _load_flow_revision_record(
        self,
        flow_id: str,
        revision: int,
    ) -> dict[str, Any] | None:
        storage = self._storage
        if storage is None or not storage.is_initialized:
            return None
        try:
            value = storage.get(self._flow_revision_key(flow_id, revision))
        except StorageNotConfiguredError:
            return None
        return value if isinstance(value, dict) else None

    def _load_latest_revision_number(self, flow_id: str) -> int | None:
        storage = self._storage
        if storage is None or not storage.is_initialized:
            return None
        try:
            value = storage.get(self._flow_latest_key(flow_id))
        except StorageNotConfiguredError:
            return None
        if isinstance(value, int):
            return value
        if isinstance(value, str) and value.isdigit():
            return int(value)
        return None

    def _append_revision_index(self, flow_id: str, revision: int) -> None:
        storage = self._require_storage()
        key = self._flow_revisions_index_key(flow_id)
        current = storage.get(key)
        numbers = list(current) if isinstance(current, list) else []
        if revision not in numbers:
            numbers.append(revision)
            storage.set(key, sorted(numbers))

    def _delete_flow_revision_record(self, flow_id: str, revision: int) -> None:
        storage = self._storage
        if storage is None or not storage.is_initialized:
            return
        try:
            storage.delete(self._flow_revision_key(flow_id, revision))
            key = self._flow_revisions_index_key(flow_id)
            current = storage.get(key)
            if isinstance(current, list):
                numbers = [item for item in current if int(item) != revision]
                storage.set(key, numbers)
        except StorageNotConfiguredError:
            return

    def _delete_latest_revision_pointer(self, flow_id: str) -> None:
        storage = self._storage
        if storage is None or not storage.is_initialized:
            return
        try:
            storage.delete(self._flow_latest_key(flow_id))
            storage.delete(self._flow_revisions_index_key(flow_id))
        except StorageNotConfiguredError:
            return

    def _index_process(self, process: ProcessDefinition) -> None:
        self._processes_by_id[process.definition_id] = process
        self._processes_by_name[process.name] = process

    def _unindex_process(self, process: ProcessDefinition) -> None:
        self._processes_by_id.pop(process.definition_id, None)
        if self._processes_by_name.get(process.name) is process:
            self._processes_by_name.pop(process.name, None)

    def _index_schema(self, schema: StateSchemaDefinition) -> None:
        self._schemas_by_id[schema.definition_id] = schema
        self._schemas_by_name[schema.name] = schema

    def _unindex_schema(self, schema: StateSchemaDefinition) -> None:
        self._schemas_by_id.pop(schema.definition_id, None)
        if self._schemas_by_name.get(schema.name) is schema:
            self._schemas_by_name.pop(schema.name, None)

    def _index_resource(self, resource: ResourceDefinition) -> None:
        self._resources_by_id[resource.definition_id] = resource
        self._resources_by_name[resource.name] = resource

    def _unindex_resource(self, resource: ResourceDefinition) -> None:
        self._resources_by_id.pop(resource.definition_id, None)
        if self._resources_by_name.get(resource.name) is resource:
            self._resources_by_name.pop(resource.name, None)

    def _key(self, kind: str, definition_id: str) -> str:
        return f"{self._prefix}:{kind}:{definition_id}"

    def _index_key(self, kind: str) -> str:
        return f"{self._prefix}:index:{kind}"

    def _load_record(self, kind: str, definition_id: str) -> dict[str, Any] | None:
        storage = self._storage
        if storage is None or not storage.is_initialized:
            return None
        try:
            value = storage.get(self._key(kind, definition_id))
        except StorageNotConfiguredError:
            return None
        return value if isinstance(value, dict) else None

    def _delete_record(self, kind: str, definition_id: str) -> None:
        storage = self._storage
        if storage is None or not storage.is_initialized:
            return
        try:
            storage.delete(self._key(kind, definition_id))
            self._remove_from_index(kind, definition_id)
        except StorageNotConfiguredError:
            return

    def _update_index(self, kind: str, definition_id: str) -> None:
        storage = self._require_storage()
        key = self._index_key(kind)
        current = storage.get(key)
        ids = list(current) if isinstance(current, list) else []
        if definition_id not in ids:
            ids.append(definition_id)
            storage.set(key, ids)

    def _remove_from_index(self, kind: str, definition_id: str) -> None:
        storage = self._storage
        if storage is None or not storage.is_initialized:
            return
        try:
            key = self._index_key(kind)
            current = storage.get(key)
            if not isinstance(current, list):
                return
            ids = [item for item in current if item != definition_id]
            storage.set(key, ids)
        except StorageNotConfiguredError:
            return

    def _collect_ids(self, kind: str, memory: dict[str, Any]) -> list[str]:
        ids = set(memory.keys())
        storage = self._storage
        if storage is not None and storage.is_initialized:
            try:
                indexed = storage.get(self._index_key(kind))
                if isinstance(indexed, list):
                    ids.update(str(item) for item in indexed)
            except StorageNotConfiguredError:
                pass
        return sorted(ids)

    def _definition_memory(self, kind: str) -> dict[str, Any]:
        if kind == "process":
            return self._processes_by_id
        if kind == "state_schema":
            return self._schemas_by_id
        if kind == "resource":
            return self._resources_by_id
        return self._flows_by_id

    def _scan_storage_for_name(
        self, kind: str, name: str
    ) -> FlowDefinition | ProcessDefinition | ResourceDefinition | StateSchemaDefinition | None:
        ids = self._collect_ids(kind, self._definition_memory(kind))
        for definition_id in ids:
            if kind == "flow":
                try:
                    flow = self.get_flow_by_id(definition_id)
                except DefinitionNotFoundError:
                    continue
                if flow.name == name:
                    return flow
                continue
            record = self._load_record(kind, definition_id)
            if not isinstance(record, dict):
                continue
            if str(record.get("name")) != name:
                continue
            if kind == "state_schema":
                return StateSchemaDefinition.from_dict(record)
            if kind == "resource":
                return ResourceDefinition.from_dict(record)
            return ProcessDefinition.from_dict(record)
        return None

    def _require_storage(self) -> StorageEngine:
        if self._storage is None or not self._storage.is_initialized:
            raise StorageNotConfiguredError(
                "StorageEngine is not initialized; cannot persist definitions"
            )
        return self._storage
