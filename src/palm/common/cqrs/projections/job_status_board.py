"""
Job status board projection — live orchestration job read model.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any

from palm.common.cqrs.projection import Projection
from palm.common.cqrs.query import GetJobStatusQuery, ListJobStatusQuery
from palm.common.cqrs.rebuild import ProjectionRebuildPolicy
from palm.core.orchestration.events import OrchestrationEventType

if TYPE_CHECKING:
    from palm.core.event import Event
    from palm.core.storage import StorageEngine

_PROJECTION_KEY = "palm:projections:job_status_board"
_HANDLED = frozenset(
    {
        OrchestrationEventType.JOB_SUBMITTED,
        OrchestrationEventType.JOB_STATUS_CHANGED,
        OrchestrationEventType.JOB_COMPLETED,
    }
)


@dataclass(frozen=True)
class JobStatusReadModel:
    job_id: str
    status: str
    instance_id: str | None = None
    updated_at: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> JobStatusReadModel:
        return cls(
            job_id=str(data.get("job_id", "")),
            status=str(data.get("status", "")),
            instance_id=data.get("instance_id"),
            updated_at=str(data.get("updated_at", "")),
        )


class JobStatusBoardProjection(Projection):
    """Tracks orchestration job status for host-level dashboards."""

    def __init__(self, storage: StorageEngine) -> None:
        self._storage = storage
        self._entries: dict[str, JobStatusReadModel] = {}
        self._rebuild_skipped = False
        self._load()

    @property
    def name(self) -> str:
        return "job_status_board"

    def handles(self, event_type: str) -> bool:
        return event_type in _HANDLED

    def apply(self, event: Event) -> None:
        payload = event.enriched_payload()
        job_id = payload.get("job_id")
        if not job_id:
            return

        current = self._entries.get(str(job_id))
        status = str(payload.get("status") or (current.status if current else "PENDING"))
        instance_id = payload.get("instance_id")
        if instance_id is None and event.context is not None:
            instance_id = event.context.instance_id

        self._entries[str(job_id)] = JobStatusReadModel(
            job_id=str(job_id),
            status=status,
            instance_id=str(instance_id)
            if instance_id is not None
            else (current.instance_id if current else None),
            updated_at=_now_iso(),
        )
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

    def get_job(self, query: GetJobStatusQuery) -> JobStatusReadModel | None:
        return self._entries.get(query.job_id)

    def list_jobs(self, query: ListJobStatusQuery) -> list[JobStatusReadModel]:
        rows = list(self._entries.values())
        if query.status is not None:
            rows = [row for row in rows if row.status == query.status]
        rows.sort(key=lambda row: row.updated_at, reverse=True)
        if query.limit is not None:
            rows = rows[: query.limit]
        return rows

    def _load(self) -> None:
        if not self._storage.is_initialized:
            return
        raw = self._storage.get(_PROJECTION_KEY)
        if not isinstance(raw, dict):
            return
        entries = raw.get("entries")
        if not isinstance(entries, dict):
            return
        for job_id, record in entries.items():
            if isinstance(record, dict):
                self._entries[str(job_id)] = JobStatusReadModel.from_dict(record)

    def _persist(self) -> None:
        if not self._storage.is_initialized:
            return
        self._storage.set(
            _PROJECTION_KEY,
            {
                "entries": {job_id: row.to_dict() for job_id, row in self._entries.items()},
                "updated_at": _now_iso(),
            },
        )


def _now_iso() -> str:
    return datetime.now(UTC).isoformat()
