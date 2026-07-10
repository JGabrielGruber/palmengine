"""System inspect actions for the Palm provider (local + remote).

Read-only catalog surfaces for analytics datasets and cross-Palm composition.
Returns tabular payloads: ``{ items: [...], count: N }``.
"""

from __future__ import annotations

from typing import Any

from palm.core.orchestration import JobStatus
from palm.core.resource.result import ProviderResult
from palm.providers.palm.bindings.orchestration.payload import job_payload
from palm.providers.palm.bindings.runtimes.wiring import get_bound_runtime
from palm.providers.palm.exceptions import PalmLocalError, PalmRemoteError
from palm.providers.palm.flow.params import PalmInvokeParams

SYSTEM_READ_ACTIONS = frozenset(
    {
        "list_jobs",
        "list_instances",
        "list_waiting",
        "list_flows",
        "list_resources",
    }
)


def is_system_read_action(action: str) -> bool:
    return str(action or "").strip().lower() in SYSTEM_READ_ACTIONS


def invoke_system_read(
    *,
    name: str,
    action: str,
    params: PalmInvokeParams,
    resource_id: str | None = None,
) -> ProviderResult:
    """Dispatch a system read action (local runtime or remote HTTP)."""
    action_s = str(action or "").strip().lower()
    if action_s not in SYSTEM_READ_ACTIONS:
        return ProviderResult.fail(
            f"unknown system action {action!r}",
            action=action,
            provider=name,
            resource_id=resource_id,
        )
    try:
        if params.is_remote:
            items = _remote_list(action_s, params)
        else:
            items = _local_list(action_s, params)
    except (PalmLocalError, PalmRemoteError) as exc:
        return ProviderResult.fail(
            str(exc),
            action=action_s,
            provider=name,
            resource_id=resource_id,
        )
    except Exception as exc:  # noqa: BLE001
        return ProviderResult.fail(
            str(exc),
            action=action_s,
            provider=name,
            resource_id=resource_id,
        )
    return ProviderResult.ok(
        {"items": items, "count": len(items)},
        action=action_s,
        provider=name,
        resource_id=resource_id or action_s,
        mode="remote" if params.is_remote else "local",
    )


def _limit(params: PalmInvokeParams) -> int | None:
    raw = params.extras.get("limit")
    if raw is None:
        return None
    try:
        return max(0, int(raw))
    except (TypeError, ValueError):
        return None


def _status_filter(params: PalmInvokeParams) -> str | None:
    return (
        str(params.extras["status"])
        if params.extras.get("status") is not None
        else None
    )


def _local_list(action: str, params: PalmInvokeParams) -> list[dict[str, Any]]:
    runtime = get_bound_runtime()
    if runtime is None:
        raise PalmLocalError("no bound runtime for local palm system inspect")
    limit = _limit(params)
    status = _status_filter(params)

    if action == "list_jobs":
        jobs = runtime.orchestration.list_jobs()
        rows = [job_payload(j) for j in jobs]
        if status:
            rows = [r for r in rows if r.get("status") == status]
        # flatten useful metadata fields for analytics
        out = []
        for r in rows:
            meta = r.get("metadata") if isinstance(r.get("metadata"), dict) else {}
            out.append(
                {
                    "job_id": r.get("job_id"),
                    "instance_id": r.get("instance_id") or meta.get("instance_id"),
                    "status": r.get("status"),
                    "flow_name": meta.get("flow") or meta.get("flow_name"),
                    "error": r.get("error"),
                }
            )
        return out[:limit] if limit is not None else out

    if action == "list_waiting":
        jobs = runtime.orchestration.list_jobs(status=JobStatus.WAITING_FOR_INPUT)
        out = []
        for j in jobs:
            meta = dict(j.metadata or {})
            out.append(
                {
                    "job_id": j.id,
                    "instance_id": meta.get("instance_id"),
                    "status": j.status.value,
                    "flow_name": meta.get("flow") or meta.get("flow_name"),
                    "step": meta.get("step") or meta.get("current_step"),
                }
            )
        return out[:limit] if limit is not None else out

    if action == "list_instances":
        manager = getattr(runtime, "instance_manager", None)
        if manager is None:
            raise PalmLocalError("runtime has no instance_manager")
        summaries = manager.list_summaries()
        flow_name = params.extras.get("flow_name") or params.flow_name
        rows = []
        for s in summaries:
            row = {
                "instance_id": s.instance_id,
                "job_id": s.job_id,
                "status": s.status,
                "flow_name": s.flow_name,
                "process_name": s.process_name,
            }
            if status and row["status"] != status:
                continue
            if flow_name and row.get("flow_name") != flow_name:
                continue
            rows.append(row)
        return rows[:limit] if limit is not None else rows

    if action == "list_flows":
        repo = getattr(runtime, "repository", None)
        if repo is None:
            raise PalmLocalError("runtime has no repository")
        flows = repo.list_flows()
        rows = []
        for f in flows:
            rows.append(
                {
                    "name": getattr(f, "name", None),
                    "id": getattr(f, "definition_id", None) or getattr(f, "id", None),
                    "pattern": getattr(f, "pattern", None),
                }
            )
        q = str(params.extras.get("query") or "").strip().lower()
        if q:
            rows = [r for r in rows if q in str(r.get("name") or "").lower()]
        return rows[:limit] if limit is not None else rows

    if action == "list_resources":
        repo = getattr(runtime, "repository", None)
        if repo is None:
            raise PalmLocalError("runtime has no repository")
        resources = repo.list_resources()
        rows = []
        for r in resources:
            rows.append(
                {
                    "name": getattr(r, "name", None),
                    "id": getattr(r, "definition_id", None) or getattr(r, "id", None),
                    "provider": getattr(r, "provider", None),
                    "action": getattr(r, "action", None),
                }
            )
        return rows[:limit] if limit is not None else rows

    raise PalmLocalError(f"unhandled system action {action}")


def _remote_list(action: str, params: PalmInvokeParams) -> list[dict[str, Any]]:
    from palm.providers.palm.flow.remote import client as remote_client

    base = params.remote_url or ""
    token = params.remote_token
    timeout = max(params.wait_timeout, 10.0)
    retries = params.remote_retries
    limit = _limit(params)
    status = _status_filter(params)

    path_map = {
        "list_jobs": "/v1/api/system/jobs",
        "list_waiting": "/v1/api/system/jobs",
        "list_instances": "/v1/api/system/instances",
        "list_flows": "/v1/api/definitions/flows",
        "list_resources": "/v1/api/definitions/resources",
    }
    path = path_map[action]
    # query string
    qs: list[str] = []
    if action == "list_waiting":
        qs.append("status=WAITING_FOR_INPUT")
    elif status:
        qs.append(f"status={status}")
    if limit is not None:
        qs.append(f"limit={limit}")
    if params.extras.get("flow_name") or params.flow_name:
        fn = params.extras.get("flow_name") or params.flow_name
        qs.append(f"flow_name={fn}")
    if qs:
        path = f"{path}?{'&'.join(qs)}"

    code, payload = remote_client._request_with_retry(  # noqa: SLF001 — shared client
        base,
        "GET",
        path,
        token=token,
        timeout=timeout,
        retries=retries,
    )
    if code != 200:
        raise PalmRemoteError(f"remote {action} failed: HTTP {code}")
    return _items_from_remote_payload(payload, action=action)


def _items_from_remote_payload(payload: Any, *, action: str) -> list[dict[str, Any]]:
    if not isinstance(payload, dict):
        return []
    # common list envelopes
    for key in ("jobs", "instances", "flows", "resources", "items", "data"):
        val = payload.get(key)
        if isinstance(val, list):
            return [x if isinstance(x, dict) else {"value": x} for x in val]
    if isinstance(payload.get("job"), dict):
        return [payload["job"]]
    return []


__all__ = [
    "SYSTEM_READ_ACTIONS",
    "invoke_system_read",
    "is_system_read_action",
]
