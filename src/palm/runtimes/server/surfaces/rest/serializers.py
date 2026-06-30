"""REST serializers — snapshot response shapes."""

from __future__ import annotations

from typing import Any

from palm.instances import StateSnapshot

__all__ = ["snapshot_detail", "snapshot_summary"]


def snapshot_summary(index: int, snapshot: StateSnapshot) -> dict[str, Any]:
    return {
        "snapshot_id": str(index),
        "status": snapshot.status,
        "recorded_at": snapshot.recorded_at,
        "job_id": snapshot.job_id,
        "current_step_slug": snapshot.current_step_slug,
    }


def snapshot_detail(index: int, snapshot: StateSnapshot) -> dict[str, Any]:
    return {
        "snapshot_id": str(index),
        **snapshot.to_dict(),
    }