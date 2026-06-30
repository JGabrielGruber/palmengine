"""
Wizard progress projection — step trail and backtrack undo trace.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any

from palm.common.cqrs.projection import Projection
from palm.common.cqrs.rebuild import ProjectionRebuildPolicy
from palm.patterns.wizard.bindings.cqrs.queries import (
    GetWizardProgressQuery,
    ListWizardProgressQuery,
)

if TYPE_CHECKING:
    from palm.core.event import Event
    from palm.core.storage import StorageEngine

_PROJECTION_KEY = "palm:projections:wizard_progress"
_STEP_STARTED = "wizard.step.started"
_STEP_COMPLETED = "wizard.step.completed"
_BACKTRACK_REQUESTED = "wizard.backtrack.requested"
_BACKTRACK_EXECUTED = "wizard.backtrack.executed"
_BACKTRACK_BLOCKED = "wizard.backtrack.blocked"
_COMMIT_STARTED = "wizard.commit.started"
_COMMIT_SUCCEEDED = "wizard.commit.succeeded"
_COMMIT_FAILED = "wizard.commit.failed"
_HANDLED = frozenset(
    {
        _STEP_STARTED,
        _STEP_COMPLETED,
        _BACKTRACK_REQUESTED,
        _BACKTRACK_EXECUTED,
        _BACKTRACK_BLOCKED,
        _COMMIT_STARTED,
        _COMMIT_SUCCEEDED,
        _COMMIT_FAILED,
    }
)
_MAX_TRACE = 50


@dataclass
class BacktrackTraceEntry:
    """Single undo-style backtrack record."""

    from_step: str | None
    to_step: str | None
    event_type: str
    recorded_at: str
    blocked: bool = False
    reason: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> BacktrackTraceEntry:
        return cls(
            from_step=data.get("from_step"),
            to_step=data.get("to_step"),
            event_type=str(data.get("event_type", "")),
            recorded_at=str(data.get("recorded_at", "")),
            blocked=bool(data.get("blocked")),
            reason=data.get("reason"),
        )


@dataclass
class WizardProgressReadModel:
    """Per wizard execution progress and backtrack trace."""

    key: str
    instance_id: str | None = None
    job_id: str | None = None
    wizard_name: str | None = None
    current_step: str | None = None
    completed_steps: list[str] = field(default_factory=list)
    backtrack_trace: list[BacktrackTraceEntry] = field(default_factory=list)
    commit_status: str | None = None
    commit_hook: str | None = None
    commit_error: str | None = None
    updated_at: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "key": self.key,
            "instance_id": self.instance_id,
            "job_id": self.job_id,
            "wizard_name": self.wizard_name,
            "current_step": self.current_step,
            "completed_steps": list(self.completed_steps),
            "backtrack_trace": [entry.to_dict() for entry in self.backtrack_trace],
            "commit_status": self.commit_status,
            "commit_hook": self.commit_hook,
            "commit_error": self.commit_error,
            "updated_at": self.updated_at,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> WizardProgressReadModel:
        trace_raw = data.get("backtrack_trace")
        trace: list[BacktrackTraceEntry] = []
        if isinstance(trace_raw, list):
            trace = [
                BacktrackTraceEntry.from_dict(item) for item in trace_raw if isinstance(item, dict)
            ]
        completed = data.get("completed_steps")
        return cls(
            key=str(data.get("key", "")),
            instance_id=data.get("instance_id"),
            job_id=data.get("job_id"),
            wizard_name=data.get("wizard_name"),
            current_step=data.get("current_step"),
            completed_steps=list(completed) if isinstance(completed, list) else [],
            backtrack_trace=trace,
            commit_status=data.get("commit_status"),
            commit_hook=data.get("commit_hook"),
            commit_error=data.get("commit_error"),
            updated_at=str(data.get("updated_at", "")),
        )


class WizardProgressProjection(Projection):
    """Tracks wizard step flow and backtracking for query-side inspection."""

    def __init__(self, storage: StorageEngine) -> None:
        self._storage = storage
        self._entries: dict[str, WizardProgressReadModel] = {}
        self._rebuild_skipped = False
        self._load()

    @property
    def name(self) -> str:
        return "wizard_progress"

    def handles(self, event_type: str) -> bool:
        return event_type in _HANDLED

    def apply(self, event: Event) -> None:
        payload = event.enriched_payload()
        key = self._resolve_key(payload, event)
        if key is None:
            return

        entry = self._entries.get(key) or WizardProgressReadModel(
            key=key,
            instance_id=_str_or_none(payload.get("instance_id")),
            job_id=_str_or_none(payload.get("job_id")),
        )
        if event.context is not None:
            entry.instance_id = entry.instance_id or event.context.instance_id
            entry.job_id = entry.job_id or event.context.job_id

        wizard_name = payload.get("wizard")
        if isinstance(wizard_name, str):
            entry.wizard_name = wizard_name

        if event.type == _STEP_STARTED:
            slug = payload.get("slug")
            if isinstance(slug, str):
                entry.current_step = slug
        elif event.type == _STEP_COMPLETED:
            slug = payload.get("slug")
            if isinstance(slug, str):
                entry.current_step = slug
                if slug not in entry.completed_steps:
                    entry.completed_steps.append(slug)
        elif event.type == _BACKTRACK_REQUESTED:
            entry.backtrack_trace.append(
                BacktrackTraceEntry(
                    from_step=_str_or_none(payload.get("from_step")),
                    to_step=_str_or_none(payload.get("to_slug")),
                    event_type=event.type,
                    recorded_at=_now_iso(),
                )
            )
        elif event.type == _BACKTRACK_EXECUTED:
            to_step = _str_or_none(payload.get("to_slug") or payload.get("slug"))
            entry.current_step = to_step
            entry.backtrack_trace.append(
                BacktrackTraceEntry(
                    from_step=_str_or_none(payload.get("from_step")),
                    to_step=to_step,
                    event_type=event.type,
                    recorded_at=_now_iso(),
                )
            )
        elif event.type == _BACKTRACK_BLOCKED:
            entry.backtrack_trace.append(
                BacktrackTraceEntry(
                    from_step=entry.current_step,
                    to_step=_str_or_none(payload.get("target")),
                    event_type=event.type,
                    recorded_at=_now_iso(),
                    blocked=True,
                    reason="protected_step",
                )
            )
        elif event.type == _COMMIT_STARTED:
            entry.commit_status = "started"
            entry.commit_hook = _str_or_none(payload.get("hook"))
            entry.commit_error = None
        elif event.type == _COMMIT_SUCCEEDED:
            entry.commit_status = "succeeded"
            entry.commit_hook = _str_or_none(payload.get("hook"))
            entry.commit_error = None
        elif event.type == _COMMIT_FAILED:
            entry.commit_status = "failed"
            entry.commit_hook = _str_or_none(payload.get("hook"))
            entry.commit_error = _str_or_none(payload.get("error"))

        entry.backtrack_trace = entry.backtrack_trace[-_MAX_TRACE:]
        entry.updated_at = _now_iso()
        self._entries[key] = entry
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

    def get_progress(self, query: GetWizardProgressQuery) -> WizardProgressReadModel | None:
        if query.instance_id is not None:
            for entry in self._entries.values():
                if entry.instance_id == query.instance_id:
                    return entry
        if query.job_id is not None:
            return self._entries.get(query.job_id)
        return None

    def list_progress(self, query: ListWizardProgressQuery) -> list[WizardProgressReadModel]:
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
        wizard = payload.get("wizard")
        if isinstance(wizard, str):
            return f"wizard:{wizard}"
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
                self._entries[str(key)] = WizardProgressReadModel.from_dict(record)

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


def _str_or_none(value: object) -> str | None:
    return str(value) if value is not None else None


def _now_iso() -> str:
    return datetime.now(UTC).isoformat()


__all__ = [
    "BacktrackTraceEntry",
    "WizardProgressProjection",
    "WizardProgressReadModel",
]
