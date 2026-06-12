"""
Wizard instance persistence — step slugs, BT position, and resume state restoration.

Wizard-specific extensions for durable ``ProcessInstance`` records. Generic
snapshot and instance shell logic lives in ``palm.common.persistence.instance_sync``;
this module is registered via :func:`~palm.patterns._registry.register_instance_sync`.
"""

from __future__ import annotations

from typing import Any

from palm.core.orchestration import Job
from palm.instances import ProcessInstance
from palm.patterns.wizard.keys import WizardKeys
from palm.patterns.wizard.pattern import WizardPattern
from palm.patterns.wizard.resume import restore_wizard_position, wizard_runtime_position
from palm.states import BlackboardState


def extract_instance_fields_from_job(job: Job) -> tuple[str | None, dict[str, Any]]:
    """Return wizard step slug and runtime position for instance persistence."""
    return wizard_step_slug_for_job(job), wizard_runtime_position_for_job(job)


def wizard_step_slug_for_job(job: Job) -> str | None:
    """Resolve the current wizard step slug from a live job."""
    if not isinstance(job.executable, WizardPattern):
        slug = job.state.get(WizardKeys.CURRENT_STEP)
        return str(slug) if slug is not None else None
    return job.executable.current_step_slug(job.state)


def wizard_runtime_position_for_job(job: Job) -> dict[str, Any]:
    """Capture behavior-tree position metadata for instance persistence."""
    if isinstance(job.executable, WizardPattern):
        return wizard_runtime_position(job.executable, job.state)
    return {}


def prepare_wizard_resume_state(
    instance: ProcessInstance,
    executable: Any,
    state: BlackboardState,
) -> BlackboardState:
    """Restore wizard tree position after loading a persisted blackboard snapshot."""
    if isinstance(executable, WizardPattern):
        restore_wizard_position(executable, state)
        if instance.runtime_position.get("sequence_index") is not None:
            idx = instance.runtime_position["sequence_index"]
            if isinstance(idx, int):
                executable._sequence._current_index = idx
    return state