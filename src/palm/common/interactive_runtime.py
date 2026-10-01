"""
Interactive runtime helpers — resolve instances, deliver input, and request backtrack.

Pattern hooks come from the ``interactive_runtime`` table the caller passes.
A missing pattern name raises. This module does not read the process table.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from palm.common.exceptions import InstanceNotFoundError
from palm.common.patterns._registry import InteractiveRuntimeHooks
from palm.core.orchestration import Job, JobStatus
from palm.core.orchestration.exceptions import JobNotFoundError
from palm.core.registry import Registry

if TYPE_CHECKING:
    from palm.system.runtime.base import BaseRuntime


def _pattern_name(job: Job) -> str:
    return str(job.metadata.get("pattern") or "")


def _interactive_hooks(
    job: Job,
    hooks: Registry[InteractiveRuntimeHooks],
) -> InteractiveRuntimeHooks:
    """Return the pattern hooks from ``hooks``. A missing name raises."""
    return hooks.get(_pattern_name(job))


def resolve_interactive_job(runtime: BaseRuntime, instance_id: str) -> Job:
    """Load (or resume) the live interactive job for a durable instance."""
    try:
        instance = runtime.get_instance(instance_id)
    except InstanceNotFoundError as exc:
        raise exc

    job_id = instance.job_id
    try:
        return runtime.get_job(job_id)
    except JobNotFoundError:
        return runtime.resume_process(instance_id)


def require_interactive_job(
    job: Job,
    instance_id: str,
    *,
    hooks: Registry[InteractiveRuntimeHooks],
) -> Any:
    """Return the executable when ``hooks`` says this job is interactive.

    ``hooks`` is the system ``interactive_runtime`` table. A missing pattern
    name raises. The process table is not a fallback.
    """
    executable = job.executable
    bound = _interactive_hooks(job, hooks)
    if not bound.is_executable(executable):
        raise TypeError(f"Instance {instance_id!r} is not an interactive flow")
    return executable


def provide_interactive_input_for_instance(
    runtime: BaseRuntime,
    instance_id: str,
    value: Any,
    *,
    hooks: Registry[InteractiveRuntimeHooks],
) -> tuple[Job, str | None]:
    """Deliver input to a waiting interactive flow and persist the updated job.

    ``hooks`` is the system ``interactive_runtime`` table. A missing pattern
    name raises. The process table is not a fallback.
    """
    job = resolve_interactive_job(runtime, instance_id)
    require_interactive_job(job, instance_id, hooks=hooks)
    if job.status != JobStatus.WAITING_FOR_INPUT:
        raise RuntimeError(
            f"Instance {instance_id!r} is not waiting for input (status={job.status.value})"
        )

    slug = runtime.provide_input(job.id, value)
    job = runtime.get_job(job.id)
    runtime.executor.persist_job(job)
    return job, slug


def request_interactive_backtrack_for_instance(
    runtime: BaseRuntime,
    instance_id: str,
    to_step: str | None,
    *,
    hooks: Registry[InteractiveRuntimeHooks],
) -> tuple[Job, str]:
    """Queue backtrack, resume execution, and persist the updated job.

    ``hooks`` is the system ``interactive_runtime`` table. A missing pattern
    name raises. The process table is not a fallback.
    """
    job = resolve_interactive_job(runtime, instance_id)
    executable = require_interactive_job(job, instance_id, hooks=hooks)
    bound = _interactive_hooks(job, hooks)
    target = to_step if to_step is not None else bound.previous_step(executable, job.state)

    executable.request_backtrack(job.state, target)
    runtime.execution.resume_job(job.id)
    job = runtime.get_job(job.id)
    runtime.executor.persist_job(job)
    return job, target


def previous_interactive_step(
    executable: Any,
    state: Any,
    *,
    pattern: str,
    hooks: Registry[InteractiveRuntimeHooks],
) -> str:
    """Return the slug of the step immediately before the current position.

    ``hooks`` is the system ``interactive_runtime`` table. A missing pattern
    name raises. The process table is not a fallback.
    """
    return hooks.get(pattern).previous_step(executable, state)


__all__ = [
    "provide_interactive_input_for_instance",
    "previous_interactive_step",
    "request_interactive_backtrack_for_instance",
    "require_interactive_job",
    "resolve_interactive_job",
]
