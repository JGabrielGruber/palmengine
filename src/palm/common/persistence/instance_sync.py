"""
Sync orchestration jobs with durable ``ProcessInstance`` records.

Generic snapshot and instance shell logic only. Pattern-specific field
extraction and resume restoration are an ``instance_sync`` registry on the
system instance. This module does not read the process-wide tables.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, cast

from palm.common.persistence.instance_migration_metadata import preserve_migration_metadata
from palm.common.persistence.state_snapshot import (
    snapshot_meta,
    snapshot_state,
    state_from_snapshot,
)
from palm.core.orchestration import Job
from palm.core.registry import Registry
from palm.core.wait import rehydrate_wait_interests
from palm.definitions.flow import FlowDefinition
from palm.instances import ProcessInstance
from palm.states import BlackboardState

InstanceFieldsFn = Callable[[Job], tuple[str | None, dict[str, Any]]]
ResumeStateFn = Callable[[ProcessInstance, Any, BlackboardState], BlackboardState]


@dataclass(frozen=True)
class InstanceSyncHooks:
    """Field extractor and resume handler for one pattern."""

    fields: InstanceFieldsFn
    resume: ResumeStateFn


def instance_sync_from(registries: Any) -> Registry[InstanceSyncHooks] | None:
    """Return the installed ``instance_sync`` table, or none when it is absent."""
    if registries is None or "instance_sync" not in registries.names():
        return None
    return cast(Registry[InstanceSyncHooks], registries.require("instance_sync"))


__all__ = [
    "InstanceSyncHooks",
    "build_instance_from_job",
    "instance_sync_from",
    "prepare_resume_state",
    "session_id_from_job_metadata",
    "snapshot_state",
    "state_from_snapshot",
    "update_instance_from_job",
]


def session_id_from_job_metadata(metadata: dict[str, Any] | None) -> str | None:
    """Extract system session id from job metadata (0.58.4 / 0.58.9).

    One key only: ``session_id`` (system subject, typically ``sess-…``).
    """
    if not metadata:
        return None
    raw = metadata.get("session_id")
    if raw is None:
        return None
    sid = str(raw).strip()
    return sid or None


def build_instance_from_job(
    job: Job,
    *,
    flow: FlowDefinition,
    instance_id: str | None = None,
    process_id: str | None = None,
    process_name: str | None = None,
    sync: Registry[InstanceSyncHooks] | None = None,
) -> ProcessInstance:
    """Create a new instance record from a submitted job."""
    iid = instance_id or str(job.metadata.get("instance_id") or job.id)
    step_slug, position = _pattern_instance_fields(job, flow.pattern, sync)
    meta = dict(job.metadata)
    session_id = session_id_from_job_metadata(meta)
    if session_id is not None:
        meta.setdefault("session_id", session_id)
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
        session_id=session_id,
        metadata=meta,
        status_history=[],
        current_step_slug=step_slug,
        runtime_position=position,
        state_meta=snapshot_meta(job.state),
    )


def update_instance_from_job(
    instance: ProcessInstance,
    job: Job,
    *,
    sync: Registry[InstanceSyncHooks] | None = None,
) -> ProcessInstance:
    """Refresh mutable fields and append status history."""
    step_slug, position = _pattern_instance_fields(job, instance.pattern, sync)
    instance.job_id = job.id
    instance.state_snapshot = snapshot_state(job.state)
    instance.metadata = preserve_migration_metadata(instance.metadata, dict(job.metadata))
    sid = session_id_from_job_metadata(instance.metadata)
    if sid is not None:
        instance.session_id = sid
        instance.metadata.setdefault("session_id", sid)
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
    *,
    sync: Registry[InstanceSyncHooks] | None = None,
) -> BlackboardState:
    """Load blackboard state and delegate pattern-specific resume restoration."""
    state = state_from_snapshot(instance.state_snapshot)
    # Continue plane: normalize palm.wait.interests after snapshot restore.
    rehydrate_wait_interests(state)
    if sync is None:
        return state
    restored = sync.get(instance.pattern).resume(instance, executable, state)
    if not isinstance(restored, BlackboardState):
        raise TypeError(f"Resume handler for {instance.pattern!r} must return BlackboardState")
    rehydrate_wait_interests(restored)
    return restored


def _pattern_instance_fields(
    job: Job,
    pattern: str,
    sync: Registry[InstanceSyncHooks] | None,
) -> tuple[str | None, dict[str, Any]]:
    """Resolve optional step slug and runtime position from ``sync``."""
    if sync is None:
        return None, {}
    return sync.get(pattern).fields(job)
