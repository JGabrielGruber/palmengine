"""Pure WorkIntent — durable deferred work request (no I/O)."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any


@dataclass(frozen=True, slots=True)
class WorkIntent:
    """Android-shaped work request: enqueue now, execute when able."""

    kind: str  # run_flow | run_process
    target: str  # flow_id or process id
    id: str = field(default_factory=lambda: uuid.uuid4().hex)
    payload: dict[str, Any] = field(default_factory=dict)
    coalesce_key: str | None = None
    not_before: str | None = None  # ISO timestamp or None = due now
    created_at: str = field(
        default_factory=lambda: datetime.now(UTC).isoformat()
    )
    attempt: int = 0
    depth: int = 0
    status: str = "pending"  # pending | claimed | done | failed
    last_error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "kind": self.kind,
            "target": self.target,
            "payload": dict(self.payload),
            "coalesce_key": self.coalesce_key,
            "not_before": self.not_before,
            "created_at": self.created_at,
            "attempt": self.attempt,
            "depth": self.depth,
            "status": self.status,
            "last_error": self.last_error,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> WorkIntent:
        return cls(
            id=str(data.get("id") or uuid.uuid4().hex),
            kind=str(data.get("kind") or "run_flow"),
            target=str(data.get("target") or ""),
            payload=dict(data.get("payload") or {}),
            coalesce_key=(
                str(data["coalesce_key"])
                if data.get("coalesce_key") is not None
                else None
            ),
            not_before=(
                str(data["not_before"])
                if data.get("not_before") is not None
                else None
            ),
            created_at=str(data.get("created_at") or datetime.now(UTC).isoformat()),
            attempt=int(data.get("attempt") or 0),
            depth=int(data.get("depth") or 0),
            status=str(data.get("status") or "pending"),
            last_error=data.get("last_error"),
        )

    def is_due(self, *, now: datetime | None = None) -> bool:
        if not self.not_before:
            return True
        try:
            due = datetime.fromisoformat(self.not_before)
        except ValueError:
            return True
        current = now or datetime.now(UTC)
        if due.tzinfo is None:
            due = due.replace(tzinfo=UTC)
        return current >= due


__all__ = ["WorkIntent"]
