"""
Resource invocation projection — per-instance/job resource call timeline.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any

from palm.common.cqrs.projection import Projection
from palm.common.cqrs.query import GetResourceInvocationsQuery, ListResourceInvocationsQuery
from palm.common.cqrs.rebuild import ProjectionRebuildPolicy

if TYPE_CHECKING:
    from palm.core.event import Event
    from palm.core.storage import StorageEngine

_PROJECTION_KEY = "palm:projections:resource_invocations"
_RESOURCE_INVOKED = "resource.invoked"
_RESOURCE_COMPLETED = "resource.completed"
_RESOURCE_FAILED = "resource.failed"
_RESOURCE_COMPENSATED = "resource.compensated"
_HANDLED = frozenset(
    {
        _RESOURCE_INVOKED,
        _RESOURCE_COMPLETED,
        _RESOURCE_FAILED,
        _RESOURCE_COMPENSATED,
    }
)
_MAX_ENTRIES = 100


@dataclass
class ResourceInvocationEntry:
    """Single resource invoke record in the read model."""

    event_type: str
    recorded_at: str
    provider: str | None = None
    action: str | None = None
    resource_ref: str | None = None
    definition_id: str | None = None
    definition_name: str | None = None
    resource_id: str | None = None
    step_slug: str | None = None
    wizard: str | None = None
    success: bool | None = None
    error: str | None = None
    mutating: bool | None = None
    invoke_depth: int | None = None
    parent_job_id: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ResourceInvocationEntry:
        return cls(
            event_type=str(data.get("event_type", "")),
            recorded_at=str(data.get("recorded_at", "")),
            provider=data.get("provider"),
            action=data.get("action"),
            resource_ref=data.get("resource_ref"),
            definition_id=data.get("definition_id"),
            definition_name=data.get("definition_name"),
            resource_id=data.get("resource_id"),
            step_slug=data.get("step_slug"),
            wizard=data.get("wizard"),
            success=data.get("success"),
            error=data.get("error"),
            mutating=data.get("mutating"),
            invoke_depth=data.get("invoke_depth"),
            parent_job_id=data.get("parent_job_id"),
        )


@dataclass
class ResourceInvocationReadModel:
    """Resource invocation trail keyed by instance or job."""

    key: str
    instance_id: str | None = None
    job_id: str | None = None
    entries: list[ResourceInvocationEntry] = field(default_factory=list)
    updated_at: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "key": self.key,
            "instance_id": self.instance_id,
            "job_id": self.job_id,
            "entries": [entry.to_dict() for entry in self.entries],
            "updated_at": self.updated_at,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ResourceInvocationReadModel:
        raw_entries = data.get("entries")
        entries: list[ResourceInvocationEntry] = []
        if isinstance(raw_entries, list):
            entries = [
                ResourceInvocationEntry.from_dict(item)
                for item in raw_entries
                if isinstance(item, dict)
            ]
        return cls(
            key=str(data.get("key", "")),
            instance_id=data.get("instance_id"),
            job_id=data.get("job_id"),
            entries=entries,
            updated_at=str(data.get("updated_at", "")),
        )


class ResourceInvocationProjection(Projection):
    """Tracks resource invocations for Explorer timelines and agent introspection."""

    def __init__(self, storage: StorageEngine) -> None:
        self._storage = storage
        self._entries: dict[str, ResourceInvocationReadModel] = {}
        self._rebuild_skipped = False
        self._load()

    @property
    def name(self) -> str:
        return "resource_invocations"

    def handles(self, event_type: str) -> bool:
        return event_type in _HANDLED

    def apply(self, event: Event) -> None:
        payload = event.enriched_payload()
        key = self._resolve_key(payload, event)
        if key is None:
            return

        entry_model = self._entries.get(key) or ResourceInvocationReadModel(
            key=key,
            instance_id=_str_or_none(payload.get("instance_id")),
            job_id=_str_or_none(payload.get("job_id")),
        )
        if event.context is not None:
            entry_model.instance_id = entry_model.instance_id or event.context.instance_id
            entry_model.job_id = entry_model.job_id or event.context.job_id

        entry_model.entries.append(_entry_from_event(event))
        entry_model.entries = entry_model.entries[-_MAX_ENTRIES:]
        entry_model.updated_at = _now_iso()
        self._entries[key] = entry_model
        self._persist()

    def entry_count(self) -> int:
        return len(self._entries)

    def was_rebuild_skipped(self) -> bool:
        return self._rebuild_skipped

    def rebuild(self, *, policy: ProjectionRebuildPolicy | None = None) -> int:
        resolved = policy or ProjectionRebuildPolicy()
        self._rebuild_skipped = False
        if resolved.skip_if_fresh and not resolved.force and self._entries:
            self._rebuild_skipped = True
            return len(self._entries)
        return len(self._entries)

    def clear(self) -> None:
        self._entries.clear()
        if self._storage.is_initialized:
            self._storage.delete(_PROJECTION_KEY)

    def get_invocations(
        self, query: GetResourceInvocationsQuery
    ) -> ResourceInvocationReadModel | None:
        if query.instance_id is not None:
            for entry in self._entries.values():
                if entry.instance_id == query.instance_id:
                    return entry
        if query.job_id is not None:
            return self._entries.get(query.job_id)
        return None

    def list_invocations(
        self, query: ListResourceInvocationsQuery
    ) -> list[ResourceInvocationReadModel]:
        rows = list(self._entries.values())
        rows.sort(key=lambda entry: entry.updated_at, reverse=True)
        if query.limit is not None:
            rows = rows[: query.limit]
        return rows

    def _resolve_key(self, payload: dict[str, Any], event: Event) -> str | None:
        if event.context is not None:
            if event.context.instance_id:
                return str(event.context.instance_id)
            if event.context.job_id:
                return str(event.context.job_id)
        instance_id = payload.get("instance_id")
        if instance_id:
            return str(instance_id)
        job_id = payload.get("job_id")
        if job_id:
            return str(job_id)
        return None

    def _load(self) -> None:
        if not self._storage.is_initialized:
            return
        raw = self._storage.get(_PROJECTION_KEY)
        if not isinstance(raw, dict):
            return
        entries = raw.get("entries")
        if not isinstance(entries, dict):
            return
        for key, record in entries.items():
            if isinstance(record, dict):
                self._entries[str(key)] = ResourceInvocationReadModel.from_dict(record)

    def _persist(self) -> None:
        if not self._storage.is_initialized:
            return
        self._storage.set(
            _PROJECTION_KEY,
            {
                "entries": {key: entry.to_dict() for key, entry in self._entries.items()},
                "updated_at": _now_iso(),
            },
        )


def _entry_from_event(event: Event) -> ResourceInvocationEntry:
    payload = event.enriched_payload()
    success = None
    if event.type == _RESOURCE_COMPLETED:
        success = True
    elif event.type in {_RESOURCE_FAILED, _RESOURCE_COMPENSATED}:
        success = event.type == _RESOURCE_COMPENSATED
    return ResourceInvocationEntry(
        event_type=event.type,
        recorded_at=_now_iso(),
        provider=_str_or_none(payload.get("provider")),
        action=_str_or_none(payload.get("action")),
        resource_ref=_str_or_none(payload.get("resource_ref")),
        definition_id=_str_or_none(payload.get("definition_id")),
        definition_name=_str_or_none(payload.get("definition_name")),
        resource_id=_str_or_none(payload.get("resource_id")),
        step_slug=_str_or_none(payload.get("step_slug")),
        wizard=_str_or_none(payload.get("wizard")),
        success=success,
        error=_str_or_none(payload.get("error")),
        mutating=bool(payload.get("mutating")) if payload.get("mutating") is not None else None,
        invoke_depth=_int_or_none(payload.get("invoke_depth")),
        parent_job_id=_str_or_none(payload.get("parent_job_id")),
    )


def _str_or_none(value: object) -> str | None:
    return str(value) if value is not None else None


def _int_or_none(value: object) -> int | None:
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _now_iso() -> str:
    return datetime.now(UTC).isoformat()