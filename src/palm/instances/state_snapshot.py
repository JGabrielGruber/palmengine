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
    current_step_slug: str | None = None
    runtime_position: dict[str, Any] = field(default_factory=dict)
    detail: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def now(cls, job: Job, **detail: Any) -> StateSnapshot:
        """Build a snapshot from the current job state."""
        from palm.common.persistence.state_snapshot import snapshot_meta, snapshot_state

        step_slug, runtime_position = _pattern_snapshot_fields(job)
        payload = {k: v for k, v in detail.items() if v is not None}
        state_meta = snapshot_meta(job.state)
        if state_meta:
            payload.setdefault("state_meta", state_meta)
        return cls(
            status=job.status.value,
            recorded_at=datetime.now(UTC).isoformat(),
            state_snapshot=snapshot_state(job.state),
            job_id=job.id,
            current_step_slug=step_slug,
            runtime_position=runtime_position,
            detail=payload,
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "recorded_at": self.recorded_at,
            "state_snapshot": dict(self.state_snapshot),
            "job_id": self.job_id,
            "current_step_slug": self.current_step_slug,
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
            current_step_slug=data.get("current_step_slug") or data.get("wizard_step_slug"),
            runtime_position=dict(data.get("runtime_position") or {}),
            detail=dict(data.get("detail") or {}),
        )


def _pattern_snapshot_fields(job: Job) -> tuple[str | None, dict[str, Any]]:
    """Resolve optional step slug and runtime position via the pattern registry."""
    import palm.patterns  # noqa: F401 — register pattern extension hooks
    from palm.common.patterns._registry import get_instance_fields

    pattern = job.metadata.get("pattern")
    if not isinstance(pattern, str):
        return None, {}
    fields_fn = get_instance_fields(pattern)
    if fields_fn is None:
        return None, {}
    return fields_fn(job)
