"""
Wizard runtime helpers — resolve instances, deliver input, and request backtrack.

Dispatches pattern-specific logic through :mod:`palm.patterns._registry` so this
module stays free of ``palm.patterns.wizard`` imports.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import palm.patterns  # noqa: F401 — ensure pattern bridge hooks are registered

from palm.common.exceptions import InstanceNotFoundError
from palm.core.orchestration import Job, JobStatus
from palm.core.orchestration.exceptions import JobNotFoundError
from palm.patterns._registry import InteractiveRuntimeHooks, get_interactive_runtime

if TYPE_CHECKING:
    from palm.common.runtimes.base import BaseRuntime


def _pattern_name(job: Job) -> str:
    return str(job.metadata.get("pattern") or "")


def _interactive_hooks(job: Job) -> InteractiveRuntimeHooks:
    name = _pattern_name(job)
    hooks = get_interactive_runtime(name)
    if hooks is None:
        raise TypeError(f"Job pattern {name!r} has no interactive runtime hooks")
    return hooks


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


def require_wizard_job(job: Job, instance_id: str) -> Any:
    executable = job.executable
    hooks = _interactive_hooks(job)
    if not hooks.is_executable(executable):
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
    hooks = _interactive_hooks(job)
    target = to_step if to_step is not None else hooks.previous_step(wizard, job.state)

    wizard.request_backtrack(job.state, target)
    runtime.orchestration.resume_job(job.id)
    job = runtime.get_job(job.id)
    runtime.executor.persist_job(job)
    return job, target


def previous_wizard_step(wizard: Any, state: Any) -> str:
    """Return the slug of the step immediately before the current position."""
    hooks = get_interactive_runtime("wizard")
    if hooks is None:
        raise RuntimeError("Wizard interactive runtime hooks are not registered")
    return hooks.previous_step(wizard, state)