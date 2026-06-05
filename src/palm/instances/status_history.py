"""
Status history entries for durable process instances.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any


@dataclass(frozen=True)
class StatusHistoryEntry:
    """One job status transition recorded on an instance."""

    status: str
    recorded_at: str
    detail: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def now(cls, status: str, **detail: Any) -> StatusHistoryEntry:
        payload = {k: v for k, v in detail.items() if v is not None}
        return cls(
            status=status,
            recorded_at=datetime.now(UTC).isoformat(),
            detail=payload,
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "recorded_at": self.recorded_at,
            "detail": dict(self.detail),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> StatusHistoryEntry:
        return cls(
            status=str(data["status"]),
            recorded_at=str(data["recorded_at"]),
            detail=dict(data.get("detail") or {}),
        )
