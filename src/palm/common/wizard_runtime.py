"""
Wizard runtime helpers — resolve instances, deliver input, and request backtrack.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from palm.common.exceptions import InstanceNotFoundError
from palm.core.orchestration import Job, JobStatus
from palm.core.orchestration.exceptions import JobNotFoundError
from palm.patterns.wizard.pattern import WizardPattern
from palm.patterns.wizard.phases.backtrack import can_backtrack_to

if TYPE_CHECKING:
    from palm.common.runtimes.base import BaseRuntime


def resolve_wizard_job(runtime: BaseRuntime, instance_id: str) -> Job:
    """Load (or resume) the live wizard job for a durable instance."""
    try:
        instance = runtime.get_instance(instance_id)
    except InstanceNotFoundError as exc:
        raise exc

    job_id = instance.job_id
    try:
        return runtime.get_job(job_id)
    except JobNotFoundError:
        return runtime.resume_process(instance_id)


def require_wizard_job(job: Job, instance_id: str) -> WizardPattern:
    executable = job.executable
    if not isinstance(executable, WizardPattern):
        raise TypeError(f"Instance {instance_id!r} is not a wizard flow")
    return executable


def provide_wizard_input_for_instance(
    runtime: BaseRuntime,
    instance_id: str,
    value: Any,
) -> tuple[Job, str | None]:
    """Deliver input to a waiting wizard and persist the updated job."""
    job = resolve_wizard_job(runtime, instance_id)
    require_wizard_job(job, instance_id)
    if job.status != JobStatus.WAITING_FOR_INPUT:
        raise RuntimeError(
            f"Wizard {instance_id!r} is not waiting for input (status={job.status.value})"
        )

    slug = runtime.provide_input(job.id, value)
    job = runtime.get_job(job.id)
    runtime.executor.persist_job(job)
    return job, slug


def request_wizard_backtrack_for_instance(
    runtime: BaseRuntime,
    instance_id: str,
    to_step: str | None,
) -> tuple[Job, str]:
    """Queue backtrack, resume execution, and persist the updated job."""
    job = resolve_wizard_job(runtime, instance_id)
    wizard = require_wizard_job(job, instance_id)
    target = to_step if to_step is not None else previous_wizard_step(wizard, job.state)

    wizard.request_backtrack(job.state, target)
    runtime.orchestration.resume_job(job.id)
    job = runtime.get_job(job.id)
    runtime.executor.persist_job(job)
    return job, target


def previous_wizard_step(wizard: WizardPattern, state: Any) -> str:
    """Return the slug of the step immediately before the current position."""
    current = wizard.current_step_slug(state)
    if current is None:
        raise ValueError("Wizard has no active step; cannot backtrack")

    config = wizard.config
    if not config.allow_backtrack:
        raise ValueError("Backtracking is disabled for this wizard")

    index = config.index_of(current)
    if index <= 0:
        raise ValueError("Already at the first step; cannot backtrack further")

    steps = config.iter_tree_steps()
    target = steps[index - 1].slug
    if not can_backtrack_to(config, target):
        raise ValueError(f"Cannot backtrack to step: {target!r}")
    return target