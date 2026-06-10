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

_DEFAULT_PREFIX = "palm:definitions"


class DefinitionRepository:
    """
    CRUD for flow and process definitions.

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
        self._processes_by_id: dict[str, ProcessDefinition] = {}
        self._processes_by_name: dict[str, ProcessDefinition] = {}

    @property
    def prefix(self) -> str:
        return self._prefix

    # ------------------------------------------------------------------
    # Flow CRUD
    # ------------------------------------------------------------------

    def register_flow(self, flow: FlowDefinition) -> FlowDefinition:
        """Register a flow in memory (does not persist)."""
        self._index_flow(flow)
        return flow

    def save_flow(self, flow: FlowDefinition) -> FlowDefinition:
        """Register and persist a flow definition."""
        self._index_flow(flow)
        storage = self._require_storage()
        storage.set(self._key("flow", flow.definition_id), flow.to_storage_record())
        self._update_index("flow", flow.definition_id)
        return flow

    def get_flow(self, ref: str, *, by_id: bool = False) -> FlowDefinition:
        """Load a flow by id (default) or by display name."""
        if by_id:
            return self.get_flow_by_id(ref)
        return self.get_flow_by_name(ref)

    def get_flow_by_id(self, definition_id: str) -> FlowDefinition:
        cached = self._flows_by_id.get(definition_id)
        if cached is not None:
            return cached
        record = self._load_record("flow", definition_id)
        if record is None:
            raise DefinitionNotFoundError("flow", definition_id)
        flow = FlowDefinition.from_dict(record)
        self._index_flow(flow)
        return flow

    def get_flow_by_name(self, name: str) -> FlowDefinition:
        cached = self._flows_by_name.get(name)
        if cached is not None:
            return cached
        for flow in self._flows_by_id.values():
            if flow.name == name:
                return flow
        loaded = self._scan_storage_for_name("flow", name)
        if loaded is not None:
            self._index_flow(loaded)
            return loaded
        raise DefinitionNotFoundError("flow", name)

    def delete_flow(self, ref: str, *, by_id: bool = True) -> bool:
        """Remove a flow from memory and storage."""
        try:
            flow = self.get_flow(ref, by_id=by_id)
        except DefinitionNotFoundError:
            return False
        self._unindex_flow(flow)
        self._delete_record("flow", flow.definition_id)
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
        if loaded is not None:
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
    # Internal indexing / storage
    # ------------------------------------------------------------------

    def _index_flow(self, flow: FlowDefinition) -> None:
        self._flows_by_id[flow.definition_id] = flow
        self._flows_by_name[flow.name] = flow

    def _unindex_flow(self, flow: FlowDefinition) -> None:
        self._flows_by_id.pop(flow.definition_id, None)
        if self._flows_by_name.get(flow.name) is flow:
            self._flows_by_name.pop(flow.name, None)

    def _index_process(self, process: ProcessDefinition) -> None:
        self._processes_by_id[process.definition_id] = process
        self._processes_by_name[process.name] = process

    def _unindex_process(self, process: ProcessDefinition) -> None:
        self._processes_by_id.pop(process.definition_id, None)
        if self._processes_by_name.get(process.name) is process:
            self._processes_by_name.pop(process.name, None)

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

    def _scan_storage_for_name(
        self, kind: str, name: str
    ) -> FlowDefinition | ProcessDefinition | None:
        ids = self._collect_ids(
            kind, self._flows_by_id if kind == "flow" else self._processes_by_id
        )
        for definition_id in ids:
            record = self._load_record(kind, definition_id)
            if not isinstance(record, dict):
                continue
            if str(record.get("name")) != name:
                continue
            if kind == "flow":
                return FlowDefinition.from_dict(record)
            return ProcessDefinition.from_dict(record)
        return None

    def _require_storage(self) -> StorageEngine:
        if self._storage is None or not self._storage.is_initialized:
            raise StorageNotConfiguredError(
                "StorageEngine is not initialized; cannot persist definitions"
            )
        return self._storage
