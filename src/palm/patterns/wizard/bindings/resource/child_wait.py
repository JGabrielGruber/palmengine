"""Nested wizard child-wait state — suspend parent until a child job finishes."""

from __future__ import annotations

from typing import Any

from palm.core.orchestration import Job, JobStatus
from palm.core.resource.result import ProviderResult
from palm.patterns.wizard.bindings.context.keys import WizardKeys


def should_wait_for_child(result: ProviderResult) -> bool:
    """Return whether a compositional invoke should park the parent wizard step."""
    if result.metadata.get("waiting_for_child_wizard"):
        return True
    data = result.data
    if isinstance(data, dict) and data.get("waiting_for_child_wizard"):
        return True
    return False


def child_wait_from_result(
    result: ProviderResult | dict[str, Any],
    *,
    step_slug: str,
    output_key: str,
    resource_ref: str | None = None,
) -> dict[str, Any]:
    """Build durable child-wait linkage from a palm provider payload."""
    data = result.data if isinstance(result, ProviderResult) else result
    if not isinstance(data, dict):
        data = {}
    child_job_id = data.get("child_job_id") or data.get("job_id")
    child_instance_id = data.get("child_instance_id") or data.get("instance_id")
    return {
        "step_slug": step_slug,
        "output_key": output_key,
        "resource_ref": resource_ref,
        "child_job_id": str(child_job_id) if child_job_id else None,
        "child_instance_id": str(child_instance_id) if child_instance_id else None,
        "child_status": str(data.get("status") or JobStatus.WAITING_FOR_INPUT.value),
        "wait_mode": data.get("wait_mode") or result.metadata.get("wait_mode")
        if isinstance(result, ProviderResult)
        else data.get("wait_mode"),
        "child_job_href": data.get("child_job_href"),
        "child_instance_href": data.get("child_instance_href"),
        "child_payload": dict(data),
    }


def get_child_wait(state: Any) -> dict[str, Any] | None:
    raw = _state_get(state, WizardKeys.WAITING_FOR_CHILD)
    return dict(raw) if isinstance(raw, dict) else None


def set_child_wait(state: Any, payload: dict[str, Any]) -> None:
    _state_set(state, WizardKeys.WAITING_FOR_CHILD, dict(payload))


def clear_child_wait(state: Any) -> None:
    deleter = getattr(state, "delete", None)
    if callable(deleter):
        deleter(WizardKeys.WAITING_FOR_CHILD)


def child_job_id_from_wait(waiting: dict[str, Any] | None) -> str | None:
    if not waiting:
        return None
    raw = waiting.get("child_job_id")
    return str(raw) if raw else None


def poll_child_job(runtime: Any, child_job_id: str) -> Job | None:
    getter = getattr(runtime, "get_job", None)
    if not callable(getter):
        return None
    try:
        return getter(child_job_id)
    except Exception:
        return None


def child_is_terminal(job: Job) -> bool:
    return job.is_terminal


def child_is_live(job: Job) -> bool:
    return job.status in (JobStatus.RUNNING, JobStatus.WAITING_FOR_INPUT)


def default_child_wait_prompt(waiting: dict[str, Any]) -> str:
    child_job_id = waiting.get("child_job_id") or "child"
    status = waiting.get("child_status") or JobStatus.WAITING_FOR_INPUT.value
    return (
        f"Waiting for nested wizard (job {child_job_id}, status={status}). "
        "Complete the child wizard to continue this step."
    )


def _state_get(state: Any, key: str) -> Any:
    getter = getattr(state, "get", None)
    return getter(key) if callable(getter) else None


def _state_set(state: Any, key: str, value: Any) -> None:
    setter = getattr(state, "set", None)
    if callable(setter):
        setter(key, value)
