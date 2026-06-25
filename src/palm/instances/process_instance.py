"""
ProcessInstance — durable snapshot of a running flow/job.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from palm.instances.state_snapshot import StateSnapshot
from palm.instances.status_history import StatusHistoryEntry

_INSTANCE_VERSION = 2


@dataclass
class ProcessInstance:
    """
    Persisted view of orchestrated work for resume and audit.

    ``instance_id`` is stable across runtime restarts; ``job_id`` links to the
    active orchestration job (may match ``instance_id`` on first submit).
    """

    instance_id: str
    job_id: str
    status: str
    state_snapshot: dict[str, Any]
    flow_definition: dict[str, Any]
    pattern: str
    flow_id: str | None = None
    flow_name: str | None = None
    process_id: str | None = None
    process_name: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    version: int = 1
    status_history: list[StatusHistoryEntry] = field(default_factory=list)
    state_snapshots: list[StateSnapshot] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.now(UTC).isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now(UTC).isoformat())
    current_step_slug: str | None = None
    runtime_position: dict[str, Any] = field(default_factory=dict)
    state_meta: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "version": _INSTANCE_VERSION,
            "kind": "process_instance",
            "instance_id": self.instance_id,
            "job_id": self.job_id,
            "status": self.status,
            "state_snapshot": dict(self.state_snapshot),
            "flow_definition": dict(self.flow_definition),
            "pattern": self.pattern,
            "flow_id": self.flow_id,
            "flow_name": self.flow_name,
            "process_id": self.process_id,
            "process_name": self.process_name,
            "metadata": dict(self.metadata),
            "version_number": self.version,
            "status_history": [entry.to_dict() for entry in self.status_history],
            "state_snapshots": [entry.to_dict() for entry in self.state_snapshots],
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "current_step_slug": self.current_step_slug,
            "runtime_position": dict(self.runtime_position),
            "state_meta": dict(self.state_meta),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ProcessInstance:
        history_raw = data.get("status_history") or []
        history = [
            StatusHistoryEntry.from_dict(item) for item in history_raw if isinstance(item, dict)
        ]
        snapshots_raw = data.get("state_snapshots") or []
        snapshots = [
            StateSnapshot.from_dict(item) for item in snapshots_raw if isinstance(item, dict)
        ]
        return cls(
            instance_id=str(data["instance_id"]),
            job_id=str(data["job_id"]),
            status=str(data["status"]),
            state_snapshot=dict(data.get("state_snapshot") or {}),
            flow_definition=dict(data.get("flow_definition") or {}),
            pattern=str(data.get("pattern", "")),
            flow_id=data.get("flow_id"),
            flow_name=data.get("flow_name"),
            process_id=data.get("process_id"),
            process_name=data.get("process_name"),
            metadata=dict(data.get("metadata") or {}),
            version=int(data.get("version_number", data.get("version", 1))),
            status_history=history,
            state_snapshots=snapshots,
            created_at=str(data.get("created_at", datetime.now(UTC).isoformat())),
            updated_at=str(data.get("updated_at", datetime.now(UTC).isoformat())),
            current_step_slug=data.get("current_step_slug") or data.get("wizard_step_slug"),
            runtime_position=dict(data.get("runtime_position") or {}),
            state_meta=dict(data.get("state_meta") or {}),
        )

    def append_status(self, status: str, **detail: Any) -> None:
        self.status_history.append(StatusHistoryEntry.now(status, **detail))
        self.status = status
        self.updated_at = datetime.now(UTC).isoformat()
        self.version += 1

    def append_state_snapshot(self, snapshot: StateSnapshot, *, max_snapshots: int = 10) -> None:
        """Attach a point-in-time snapshot, retaining only the most recent ``max_snapshots``."""
        limit = max(1, max_snapshots)
        self.state_snapshots.append(snapshot)
        if len(self.state_snapshots) > limit:
            self.state_snapshots = self.state_snapshots[-limit:]
        self.updated_at = datetime.now(UTC).isoformat()
        self.version += 1
