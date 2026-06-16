"""
Instance index projection — lightweight read model for instance queries.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any

from palm.common.cqrs.projection import Projection
from palm.common.cqrs.query import GetInstanceStatusQuery, ListInstancesQuery
from palm.core.orchestration.events import OrchestrationEventType

if TYPE_CHECKING:
    from palm.common.managers.instance_manager import InstanceManager
    from palm.core.event import Event
    from palm.core.storage import StorageEngine

_PROJECTION_KEY = "palm:projections:instance_index"
_WIZARD_STEP_COMPLETED = "wizard.step.completed"
_BACKTRACK_EXECUTED = "wizard.backtrack.executed"
_HANDLED_EVENTS = frozenset(
    {
        OrchestrationEventType.INSTANCE_CREATED,
        OrchestrationEventType.INSTANCE_STATUS_CHANGED,
        _WIZARD_STEP_COMPLETED,
        _BACKTRACK_EXECUTED,
    }
)
_TERMINAL_STATUSES = frozenset({"SUCCEEDED", "FAILED", "CANCELLED"})


@dataclass(frozen=True)
class InstanceReadModel:
    """Query-optimized view of a process instance."""

    instance_id: str
    job_id: str
    status: str
    flow_name: str | None = None
    process_name: str | None = None
    wizard_step_slug: str | None = None
    updated_at: str = ""

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> InstanceReadModel:
        return cls(
            instance_id=str(data.get("instance_id", "")),
            job_id=str(data.get("job_id", "")),
            status=str(data.get("status", "")),
            flow_name=data.get("flow_name"),
            process_name=data.get("process_name"),
            wizard_step_slug=data.get("wizard_step_slug"),
            updated_at=str(data.get("updated_at", "")),
        )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class InstanceIndexProjection(Projection):
    """
    Event-driven index of instance status for host queries.

    Falls back to :class:`~palm.common.managers.instance_manager.InstanceManager`
    summaries when rebuilding or when the projection entry is missing.
    """

    def __init__(
        self,
        storage: StorageEngine,
        instance_manager: InstanceManager,
    ) -> None:
        self._storage = storage
        self._instances = instance_manager
        self._entries: dict[str, InstanceReadModel] = {}
        self._load()

    @property
    def name(self) -> str:
        return "instance_index"

    def handles(self, event_type: str) -> bool:
        return event_type in _HANDLED_EVENTS

    def apply(self, event: Event) -> None:
        payload = event.enriched_payload()
        if event.type in {
            OrchestrationEventType.INSTANCE_CREATED,
            OrchestrationEventType.INSTANCE_STATUS_CHANGED,
        }:
            instance_id = payload.get("instance_id")
            if not instance_id:
                return
            current = self._entries.get(str(instance_id))
            flow_name = current.flow_name if current else None
            process_name = current.process_name if current else None
            wizard_step = current.wizard_step_slug if current else None
            if event.type == OrchestrationEventType.INSTANCE_CREATED:
                details = self._load_instance_details(str(instance_id))
                flow_name = details.get("flow_name", flow_name)
                process_name = details.get("process_name", process_name)
                wizard_step = details.get("wizard_step_slug", wizard_step)
            self._upsert(
                InstanceReadModel(
                    instance_id=str(instance_id),
                    job_id=str(payload.get("job_id") or (current.job_id if current else "")),
                    status=str(payload.get("status") or (current.status if current else "")),
                    flow_name=flow_name,
                    process_name=process_name,
                    wizard_step_slug=wizard_step,
                    updated_at=_now_iso(),
                )
            )
            return

        instance_id = payload.get("instance_id")
        if instance_id is None and event.context is not None:
            instance_id = event.context.instance_id
        if not instance_id:
            return

        current = self._entries.get(str(instance_id))
        if current is None:
            return

        slug = payload.get("slug")
        if not isinstance(slug, str):
            return

        self._upsert(
            InstanceReadModel(
                instance_id=current.instance_id,
                job_id=current.job_id,
                status=current.status,
                flow_name=current.flow_name,
                process_name=current.process_name,
                wizard_step_slug=slug,
                updated_at=_now_iso(),
            )
        )

    def rebuild(self) -> int:
        self._entries.clear()
        for summary in self._instances.list_summaries():
            self._entries[summary.instance_id] = InstanceReadModel(
                instance_id=summary.instance_id,
                job_id=summary.job_id,
                status=summary.status,
                flow_name=summary.flow_name,
                process_name=summary.process_name,
                wizard_step_slug=summary.wizard_step_slug,
                updated_at=summary.updated_at,
            )
        self._persist()
        return len(self._entries)

    def clear(self) -> None:
        self._entries.clear()
        if self._storage.is_initialized:
            self._storage.delete(_PROJECTION_KEY)

    def list_instances(self, query: ListInstancesQuery) -> list[InstanceReadModel]:
        rows = list(self._entries.values())
        if not query.include_terminal:
            rows = [row for row in rows if row.status not in _TERMINAL_STATUSES]
        if query.status is not None:
            rows = [row for row in rows if row.status == query.status]
        if query.flow_name is not None:
            rows = [row for row in rows if row.flow_name == query.flow_name]
        rows.sort(key=lambda row: row.updated_at, reverse=True)
        if query.limit is not None:
            rows = rows[: query.limit]
        return rows

    def get_instance(self, query: GetInstanceStatusQuery) -> InstanceReadModel | None:
        cached = self._entries.get(query.instance_id)
        if cached is not None:
            return cached
        try:
            summary = next(
                item
                for item in self._instances.list_summaries()
                if item.instance_id == query.instance_id
            )
        except StopIteration:
            return None
        model = InstanceReadModel(
            instance_id=summary.instance_id,
            job_id=summary.job_id,
            status=summary.status,
            flow_name=summary.flow_name,
            process_name=summary.process_name,
            wizard_step_slug=summary.wizard_step_slug,
            updated_at=summary.updated_at,
        )
        self._upsert(model)
        return model

    def _upsert(self, model: InstanceReadModel) -> None:
        self._entries[model.instance_id] = model
        self._persist()

    def _load(self) -> None:
        if not self._storage.is_initialized:
            return
        raw = self._storage.get(_PROJECTION_KEY)
        if not isinstance(raw, dict):
            return
        entries = raw.get("entries")
        if not isinstance(entries, dict):
            return
        for instance_id, record in entries.items():
            if isinstance(record, dict):
                self._entries[str(instance_id)] = InstanceReadModel.from_dict(record)

    def _persist(self) -> None:
        if not self._storage.is_initialized:
            return
        payload = {
            "entries": {
                instance_id: model.to_dict()
                for instance_id, model in self._entries.items()
            },
            "updated_at": _now_iso(),
        }
        self._storage.set(_PROJECTION_KEY, payload)

    def _load_instance_details(self, instance_id: str) -> dict[str, Any]:
        try:
            instance = self._instances.get(instance_id)
        except Exception:
            return {}
        return {
            "flow_name": instance.flow_name,
            "process_name": instance.process_name,
            "wizard_step_slug": instance.wizard_step_slug,
        }


def _now_iso() -> str:
    return datetime.now(UTC).isoformat()