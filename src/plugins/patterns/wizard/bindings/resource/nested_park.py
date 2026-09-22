"""Nested compositional park — open wait interest, nothing else.

No ``set_child_wait`` façade. Durable fact is ``palm.wait.interests`` with
``meta.source=nested_wizard``. Unpark is WaitPlaneService on ``runtime.event``.
"""

from __future__ import annotations

from typing import Any

from palm.system.subsystems.planes.wait.access import close_interest_for_state, open_interest_for_state
from palm.system.subsystems.planes.wait.deliver import NESTED_WIZARD_SOURCE
from palm.core.orchestration import JobStatus
from palm.core.resource.result import ProviderResult
from palm.core.wait import WAIT_KIND_JOB, WaitInterest, find_wait_interests, make_job_wait

NESTED_SOURCE = NESTED_WIZARD_SOURCE


def should_open_nested_park(result: ProviderResult) -> bool:
    """True when a provider result asks the parent to open a continue-plane park."""
    if result.metadata.get("nested_park"):
        return True
    data = result.data
    return isinstance(data, dict) and bool(data.get("nested_park"))


def park_meta_from_result(
    result: ProviderResult | dict[str, Any],
    *,
    step_slug: str,
    output_key: str,
    resource_ref: str | None = None,
) -> dict[str, Any]:
    """Build interest.meta (+ target id) from palm provider child payload."""
    data = result.data if isinstance(result, ProviderResult) else result
    if not isinstance(data, dict):
        data = {}
    child_job_id = data.get("child_job_id") or data.get("job_id")
    if not child_job_id:
        raise ValueError("nested park requires child_job_id / job_id on result")
    meta: dict[str, Any] = {
        "source": NESTED_SOURCE,
        "step_slug": step_slug,
        "output_key": output_key,
        "resource_ref": resource_ref,
        "child_instance_id": data.get("child_instance_id") or data.get("instance_id"),
        "child_status": str(data.get("status") or JobStatus.WAITING_FOR_INPUT.value),
        "wait_mode": (
            data.get("wait_mode") or result.metadata.get("wait_mode")
            if isinstance(result, ProviderResult)
            else data.get("wait_mode")
        ),
        "child_job_href": data.get("child_job_href"),
        "child_instance_href": data.get("child_instance_href"),
        "child_payload": dict(data),
    }
    meta = {k: v for k, v in meta.items() if v is not None}
    return {"target_id": str(child_job_id), "meta": meta}


def open_nested_park(state: Any, *, target_id: str, meta: dict[str, Any]) -> WaitInterest:
    """Sole park write: open continue-plane interest."""
    interest = make_job_wait(target_id, meta=dict(meta))
    return open_interest_for_state(state, interest, replace_same_target=True)


def nested_park_interest(state: Any) -> WaitInterest | None:
    """Active nested park interest for this owner, if any."""
    for w in find_wait_interests(state, kind=WAIT_KIND_JOB):
        if (w.meta or {}).get("source") == NESTED_SOURCE:
            return w
    return None


def nested_park_for_step(state: Any, step_slug: str) -> WaitInterest | None:
    interest = nested_park_interest(state)
    if interest is None:
        return None
    if (interest.meta or {}).get("step_slug") != step_slug:
        return None
    return interest


def clear_nested_park(state: Any, *, target_id: str | None = None) -> None:
    if target_id:
        close_interest_for_state(state, kind=WAIT_KIND_JOB, target_id=str(target_id))
        return
    for w in list(find_wait_interests(state, kind=WAIT_KIND_JOB)):
        if (w.meta or {}).get("source") == NESTED_SOURCE:
            close_interest_for_state(state, kind=w.kind, target_id=w.target_id)


def default_nested_prompt(interest: WaitInterest) -> str:
    status = (interest.meta or {}).get("child_status") or JobStatus.WAITING_FOR_INPUT.value
    return (
        f"Waiting for nested wizard (job {interest.target_id}, status={status}). "
        "Complete the child wizard to continue this step."
    )


__all__ = [
    "NESTED_SOURCE",
    "clear_nested_park",
    "default_nested_prompt",
    "nested_park_for_step",
    "nested_park_interest",
    "open_nested_park",
    "park_meta_from_result",
    "should_open_nested_park",
]
