"""
Sync orchestration jobs with durable ``ProcessInstance`` records.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from palm.core.context import BaseState
from palm.core.orchestration import Job
from palm.definitions.flow import FlowDefinition
from palm.instances import ProcessInstance
from palm.patterns.wizard import WizardPattern
from palm.patterns.wizard.keys import WizardKeys
from palm.patterns.wizard.resume import restore_wizard_position, wizard_runtime_position
from palm.states import BlackboardState


def snapshot_state(state: BaseState) -> dict[str, Any]:
    """Serialize execution state for storage."""
    return state.snapshot()


def state_from_snapshot(data: dict[str, Any]) -> BlackboardState:
    """Restore ``BlackboardState`` from a persisted snapshot."""
    return BlackboardState(dict(data))


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
    wizard_slug = _wizard_step_slug(job)
    position = _runtime_position(job)
    return ProcessInstance(
        instance_id=iid,
        job_id=job.id,
        status=job.status.value,
        state_snapshot=snapshot_state(job.state),
        flow_definition=flow.to_dict(),
        pattern=flow.pattern,
        flow_id=flow.definition_id,
        flow_name=flow.name,
        process_id=process_id or job.metadata.get("process_id"),
        process_name=process_name or job.metadata.get("process"),
        metadata=dict(job.metadata),
        status_history=[],
        wizard_step_slug=wizard_slug,
        runtime_position=position,
    )


def update_instance_from_job(instance: ProcessInstance, job: Job) -> ProcessInstance:
    """Refresh mutable fields and append status history."""
    instance.job_id = job.id
    instance.state_snapshot = snapshot_state(job.state)
    instance.metadata = dict(job.metadata)
    instance.wizard_step_slug = _wizard_step_slug(job)
    instance.runtime_position = _runtime_position(job)
    if instance.status != job.status.value:
        instance.append_status(
            job.status.value,
            job_id=job.id,
            wizard_step=instance.wizard_step_slug,
        )
    else:
        instance.updated_at = datetime.now(UTC).isoformat()
        instance.version += 1
    return instance


def prepare_resume_state(
    instance: ProcessInstance,
    pattern: Any,
) -> BlackboardState:
    """Load blackboard state and restore wizard tree position when applicable."""
    state = state_from_snapshot(instance.state_snapshot)
    if isinstance(pattern, WizardPattern):
        restore_wizard_position(pattern, state)
        if instance.runtime_position.get("sequence_index") is not None:
            idx = instance.runtime_position["sequence_index"]
            if isinstance(idx, int):
                pattern._sequence._current_index = idx
    return state


def wizard_step_slug_for_job(job: Job) -> str | None:
    return _wizard_step_slug(job)


def wizard_runtime_position_for_job(job: Job) -> dict[str, Any]:
    return _runtime_position(job)


def _wizard_step_slug(job: Job) -> str | None:
    if not isinstance(job.executable, WizardPattern):
        slug = job.state.get(WizardKeys.CURRENT_STEP)
        return str(slug) if slug is not None else None
    return job.executable.current_step_slug(job.state)


def _runtime_position(job: Job) -> dict[str, Any]:
    if isinstance(job.executable, WizardPattern):
        return wizard_runtime_position(job.executable, job.state)
    return {}
