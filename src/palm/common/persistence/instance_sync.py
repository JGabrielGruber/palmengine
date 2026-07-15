"""
Sync orchestration jobs with durable ``ProcessInstance`` records.

Generic snapshot and instance shell logic only. Pattern-specific field
extraction and resume restoration register via
:mod:`palm.common.patterns._registry` (e.g. wizard hooks in
``palm.patterns.wizard.bindings.instances.persistence``).
"""

from __future__ import annotations

from collections.abc import Callable
from datetime import UTC, datetime
from typing import Any

from palm.common.patterns._registry import get_instance_fields, get_resume_handler
from palm.common.persistence.instance_migration_metadata import preserve_migration_metadata
from palm.common.persistence.state_snapshot import (
    snapshot_meta,
    snapshot_state,
    state_from_snapshot,
)
from palm.core.orchestration import Job
from palm.definitions.flow import FlowDefinition
from palm.instances import ProcessInstance
from palm.states import BlackboardState

__all__ = [
    "build_instance_from_job",
    "prepare_resume_state",
    "snapshot_state",
    "state_from_snapshot",
    "update_instance_from_job",
]


def build_instance_from_job(
    job: Job,
    *,
    flow: FlowDefinition,
    instance_id: str | None = None,
    process_id: str | None = None,
    process_name: str | None = None,
) -> ProcessInstance:
    """Create a new instance record from a submitted job."""
    iid = instance_id or str(job.metadata.get("instance_id") or job.id)
    step_slug, position = _pattern_instance_fields(job, flow.pattern)
    return ProcessInstance(
        instance_id=iid,
        job_id=job.id,
        status=job.status.value,
        state_snapshot=snapshot_state(job.state),
        flow_definition=flow.to_dict(),
        pattern=flow.pattern,
        flow_id=flow.definition_id,
        flow_revision=flow.revision,
        flow_name=flow.name,
        process_id=process_id or job.metadata.get("process_id"),
        process_name=process_name or job.metadata.get("process"),
        metadata=dict(job.metadata),
        status_history=[],
        current_step_slug=step_slug,
        runtime_position=position,
        state_meta=snapshot_meta(job.state),
    )


def update_instance_from_job(instance: ProcessInstance, job: Job) -> ProcessInstance:
    """Refresh mutable fields and append status history."""
    step_slug, position = _pattern_instance_fields(job, instance.pattern)
    instance.job_id = job.id
    instance.state_snapshot = snapshot_state(job.state)
    instance.metadata = preserve_migration_metadata(instance.metadata, dict(job.metadata))
    instance.current_step_slug = step_slug
    instance.runtime_position = position
    instance.state_meta = snapshot_meta(job.state)
    if instance.status != job.status.value:
        instance.append_status(
            job.status.value,
            job_id=job.id,
            current_step=instance.current_step_slug,
        )
    else:
        instance.updated_at = datetime.now(UTC).isoformat()
        instance.version += 1
    return instance


def prepare_resume_state(
    instance: ProcessInstance,
    executable: Any,
) -> BlackboardState:
    """Load blackboard state and delegate pattern-specific resume restoration."""
    state = state_from_snapshot(instance.state_snapshot)
    handler = _resume_handler(instance.pattern)
    if handler is not None:
        restored = handler(instance, executable, state)
        if not isinstance(restored, BlackboardState):
            raise TypeError(f"Resume handler for {instance.pattern!r} must return BlackboardState")
        return restored
    return state


def _pattern_instance_fields(job: Job, pattern: str) -> tuple[str | None, dict[str, Any]]:
    """Resolve optional step slug and runtime position via the pattern registry."""

    fields_fn = get_instance_fields(pattern)
    if fields_fn is None:
        return None, {}
    return fields_fn(job)


ResumeHandler = Callable[[ProcessInstance, Any, BlackboardState], BlackboardState]


def _resume_handler(pattern: str) -> ResumeHandler | None:

    return get_resume_handler(pattern)
