"""
Wire ``EventEngine`` job events to ``InstanceRepository`` updates.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from palm.core.event import Event
from palm.core.orchestration.events import OrchestrationEventType
from palm.core.orchestration.job import JobStatus

if TYPE_CHECKING:
    from palm.executions.instance_repository import InstanceRepository
    from palm.runtimes.embedded import EmbeddedRuntime


def wire_instance_persistence(
    runtime: EmbeddedRuntime,
    instances: InstanceRepository,
) -> None:
    """Subscribe to orchestration events and persist job snapshots."""

    def _on_status_changed(event: Event) -> None:
        job_id = event.payload.get("job_id")
        if not isinstance(job_id, str):
            return
        try:
            job = runtime.orchestration.get_job(job_id)
        except Exception:
            return
        if not job.metadata.get("instance_id"):
            return
        try:
            instances.update(job)
        except Exception:
            pass

    runtime.event.subscribe(
        OrchestrationEventType.JOB_STATUS_CHANGED,
        _on_status_changed,
    )
    runtime.event.subscribe(
        OrchestrationEventType.JOB_COMPLETED,
        _on_status_changed,
    )


def is_resumable_status(status: str) -> bool:
    return status in (
        JobStatus.WAITING_FOR_INPUT.value,
        JobStatus.RUNNING.value,
        JobStatus.PENDING.value,
    )