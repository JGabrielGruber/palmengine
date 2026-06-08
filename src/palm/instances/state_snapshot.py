"""
StateSnapshot — point-in-time blackboard captures for audit and replay.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from palm.core.orchestration import Job


@dataclass(frozen=True)
class StateSnapshot:
    """Immutable record of job blackboard state at a status transition."""

    status: str
    recorded_at: str
    state_snapshot: dict[str, Any]
    job_id: str
    wizard_step_slug: str | None = None
    runtime_position: dict[str, Any] = field(default_factory=dict)
    detail: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def now(cls, job: Job, **detail: Any) -> StateSnapshot:
        """Build a snapshot from the current job state."""
        from palm.common.persistence.instance_sync import (
            snapshot_state,
            wizard_runtime_position_for_job,
            wizard_step_slug_for_job,
        )

        payload = {k: v for k, v in detail.items() if v is not None}
        return cls(
            status=job.status.value,
            recorded_at=datetime.now(UTC).isoformat(),
            state_snapshot=snapshot_state(job.state),
            job_id=job.id,
            wizard_step_slug=wizard_step_slug_for_job(job),
            runtime_position=wizard_runtime_position_for_job(job),
            detail=payload,
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "recorded_at": self.recorded_at,
            "state_snapshot": dict(self.state_snapshot),
            "job_id": self.job_id,
            "wizard_step_slug": self.wizard_step_slug,
            "runtime_position": dict(self.runtime_position),
            "detail": dict(self.detail),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> StateSnapshot:
        return cls(
            status=str(data["status"]),
            recorded_at=str(data["recorded_at"]),
            state_snapshot=dict(data.get("state_snapshot") or {}),
            job_id=str(data["job_id"]),
            wizard_step_slug=data.get("wizard_step_slug"),
            runtime_position=dict(data.get("runtime_position") or {}),
            detail=dict(data.get("detail") or {}),
        )