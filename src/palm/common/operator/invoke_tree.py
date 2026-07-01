"""
Compositional invoke tree — parent/child wizard stack for operator debugging.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from palm.common.job_context import instance_id_for_job
from palm.core.orchestration.exceptions import JobNotFoundError

if TYPE_CHECKING:
    from palm.common.runtimes.base import BaseRuntime


def build_invoke_tree(
    runtime: BaseRuntime,
    instance_id: str,
    *,
    base_url: str | None = None,
) -> dict[str, Any]:
    """Build a parent → child invoke stack rooted at the queried instance."""
    from palm.common.exceptions import InstanceNotFoundError
    from palm.common.interactive_runtime import resolve_interactive_job
    from palm.runtimes.cli.shared.job_inspect import inspect_job_json

    try:
        runtime.get_instance(instance_id)
    except InstanceNotFoundError as exc:
        raise exc

    job = resolve_interactive_job(runtime, instance_id)
    chain = _ancestor_chain(runtime, job)

    nodes = [
        _node_from_job(runtime, entry_job, entry_instance_id)
        for entry_instance_id, entry_job in chain
    ]
    root = nodes[0] if nodes else _node_from_job(runtime, job, instance_id)
    focus = nodes[-1] if nodes else root
    ancestors = nodes[:-1] if len(nodes) > 1 else []

    pattern = inspect_job_json(job)
    active_child = None
    if pattern.get("waiting_for_child"):
        child: dict[str, Any] = {}
        child_job_id = pattern.get("waiting_for_child_job_id")
        child_instance_id = pattern.get("waiting_for_child_instance_id")
        if child_job_id:
            child["job_id"] = child_job_id
        if child_instance_id:
            child["instance_id"] = child_instance_id
            child.update(_child_summary(runtime, str(child_instance_id), str(child_job_id or "")))
        child_status = pattern.get("child_status")
        if child_status:
            child["status"] = child_status
        if child:
            active_child = child

    payload: dict[str, Any] = {
        "instance_id": instance_id,
        "root": root,
        "focus": focus,
        "ancestors": ancestors,
        "active_child": active_child,
        "links": _links(instance_id, flow_id=focus.get("flow"), base_url=base_url),
    }
    return payload


def _ancestor_chain(runtime: BaseRuntime, job: Any) -> list[tuple[str, Any]]:
    """Walk ``__palm:parent_job_id`` metadata from the focus job up to the root."""
    chain: list[tuple[str, Any]] = []
    current = job
    seen: set[str] = set()

    while current.id not in seen:
        seen.add(current.id)
        chain.append((instance_id_for_job(current), current))
        parent_id = current.metadata.get("__palm:parent_job_id")
        if not parent_id:
            break
        try:
            current = runtime.get_job(str(parent_id))
        except JobNotFoundError:
            break

    chain.reverse()
    return chain


def _node_from_job(runtime: BaseRuntime, job: Any, instance_id: str) -> dict[str, Any]:
    flow = job.metadata.get("flow_name") or job.metadata.get("flow")
    step = None
    status = job.status.value

    try:
        instance = runtime.get_instance(instance_id)
        flow = instance.flow_name or flow
        step = instance.current_step_slug
        status = instance.status or status
    except Exception:
        pass

    return {
        "instance_id": instance_id,
        "job_id": job.id,
        "flow": flow,
        "step": step,
        "status": status,
    }


def _child_summary(runtime: BaseRuntime, instance_id: str, job_id: str) -> dict[str, Any]:
    summary: dict[str, Any] = {}
    try:
        instance = runtime.get_instance(instance_id)
        summary["flow"] = instance.flow_name
        summary["step"] = instance.current_step_slug
        summary["status"] = instance.status
    except Exception:
        if job_id:
            try:
                child_job = runtime.get_job(job_id)
                summary["flow"] = child_job.metadata.get("flow_name") or child_job.metadata.get(
                    "flow"
                )
                summary["status"] = child_job.status.value
            except JobNotFoundError:
                pass
    return summary


def _links(
    instance_id: str,
    *,
    flow_id: str | None,
    base_url: str | None,
) -> dict[str, str]:
    links: dict[str, str] = {
        "instance": f"/v1/instances/{instance_id}",
    }
    if flow_id:
        links["session"] = f"/v1/api/flows/{flow_id}/session/{instance_id}"
    if base_url:
        base = base_url.rstrip("/")
        links["explorer"] = f"{base}/explorer/instances/{instance_id}"
    return links


__all__ = ["build_invoke_tree"]
