"""Resume helpers for parent wizards waiting on nested child jobs."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from palm.core.orchestration import Job, JobStatus
from palm.core.orchestration.exceptions import JobNotFoundError
from palm.patterns.wizard.bindings.resource.child_wait import child_job_id_from_wait, get_child_wait, poll_child_job
from palm.patterns.wizard.bindings.context.keys import WizardKeys

if TYPE_CHECKING:
    from palm.common.runtimes.base import BaseRuntime


def bound_runtime() -> Any | None:
    """Return the in-process runtime used for compositional palm invokes."""
    from palm.providers.palm.wiring import get_bound_runtime

    return get_bound_runtime()


def parent_is_waiting_for_child(job: Job) -> bool:
    waiting = get_child_wait(job.state)
    return isinstance(waiting, dict) and bool(waiting.get("child_job_id"))


def resume_parent_after_child(runtime: BaseRuntime, child_job: Job) -> Job | None:
    """Resume a parent wizard when a correlated child job reaches a terminal state."""
    if child_job.status != JobStatus.SUCCEEDED:
        return None
    parent_id = child_job.metadata.get("__palm:parent_job_id")
    if not parent_id:
        return None
    try:
        parent = runtime.get_job(str(parent_id))
    except JobNotFoundError:
        return None
    if parent.status != JobStatus.WAITING_FOR_INPUT:
        return None
    waiting = get_child_wait(parent.state)
    child_id = child_job_id_from_wait(waiting)
    if child_id and child_id != child_job.id:
        return None
    runtime.orchestration.resume_job(parent.id)
    return runtime.get_job(parent.id)


def resume_child_wait_for_instance(runtime: BaseRuntime, instance_id: str) -> Job:
    """Manually re-poll the nested child and advance the parent wizard if ready."""
    from palm.common.wizard_runtime import resolve_wizard_job

    job = resolve_wizard_job(runtime, instance_id)
    if not parent_is_waiting_for_child(job):
        raise RuntimeError(f"Wizard {instance_id!r} is not waiting for a nested child")
    runtime.orchestration.resume_job(job.id)
    return runtime.get_job(job.id)


def poll_child_for_parent(state: Any, child_job_id: str) -> Job | None:
    runtime = bound_runtime()
    if runtime is None:
        return None
    return poll_child_job(runtime, child_job_id)