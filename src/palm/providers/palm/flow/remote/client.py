"""HTTP client for remote Palm ServerRuntime invocations."""

from __future__ import annotations

import json
import time
import urllib.error
import urllib.request
from typing import Any

from palm.core.orchestration import JobStatus
from palm.core.resource.invocation import WaitMode
from palm.providers.palm.exceptions import PalmRemoteError, PalmTimeoutError

_TRANSIENT_STATUS = frozenset({429, 502, 503, 504})


def _request(
    base_url: str,
    method: str,
    path: str,
    *,
    body: dict[str, Any] | None = None,
    token: str | None = None,
    timeout: float = 10.0,
) -> tuple[int, dict[str, Any] | str]:
    data = None
    headers = {"Accept": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    if body is not None:
        data = json.dumps(body).encode("utf-8")
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(
        f"{base_url.rstrip('/')}{path}",
        data=data,
        headers=headers,
        method=method,
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read().decode("utf-8")
            if "application/json" in resp.headers.get("Content-Type", ""):
                parsed = json.loads(raw)
                return resp.status, parsed if isinstance(parsed, dict) else {"data": parsed}
            return resp.status, raw
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode("utf-8")
        try:
            parsed = json.loads(raw)
            if isinstance(parsed, dict):
                return exc.code, parsed
        except json.JSONDecodeError:
            pass
        return exc.code, {"error": raw}
    except (urllib.error.URLError, TimeoutError) as exc:
        raise _transport_error(method, path, exc) from exc


def _request_with_retry(
    base_url: str,
    method: str,
    path: str,
    *,
    body: dict[str, Any] | None = None,
    token: str | None = None,
    timeout: float = 10.0,
    retries: int = 2,
) -> tuple[int, dict[str, Any] | str]:
    """Execute an HTTP request with basic retry for transient failures."""
    attempts = max(retries, 0) + 1
    delay = 0.05
    last_error: PalmRemoteError | None = None

    for attempt in range(attempts):
        try:
            status, payload = _request(
                base_url,
                method,
                path,
                body=body,
                token=token,
                timeout=timeout,
            )
            if status in _TRANSIENT_STATUS and attempt < attempts - 1:
                time.sleep(delay)
                delay = min(delay * 2, 0.5)
                continue
            return status, payload
        except PalmRemoteError as exc:
            last_error = exc
            if not exc.transient or attempt >= attempts - 1:
                raise
            time.sleep(delay)
            delay = min(delay * 2, 0.5)

    if last_error is not None:
        raise last_error
    raise PalmRemoteError(f"Remote request failed for {method} {path}")


def submit_flow_remote(
    base_url: str,
    flow_name: str,
    *,
    by_id: bool = False,
    job_id: str | None = None,
    token: str | None = None,
    timeout: float = 10.0,
    retries: int = 2,
) -> dict[str, Any]:
    """Submit a flow via ``POST /v1/jobs`` and return the acceptance payload."""
    body: dict[str, Any] = {"flow_name": flow_name, "by_id": by_id}
    if job_id is not None:
        body["job_id"] = job_id
    status, payload = _request_with_retry(
        base_url,
        "POST",
        "/v1/jobs",
        body=body,
        token=token,
        timeout=timeout,
        retries=retries,
    )
    if status not in {200, 202} or not isinstance(payload, dict):
        raise _remote_error("Remote flow submit failed", status, payload)
    return payload


def get_job_remote(
    base_url: str,
    job_id: str,
    *,
    token: str | None = None,
    timeout: float = 10.0,
    retries: int = 2,
) -> dict[str, Any]:
    """Fetch job status via ``GET /v1/jobs/{job_id}``."""
    status, payload = _request_with_retry(
        base_url,
        "GET",
        f"/v1/jobs/{job_id}",
        token=token,
        timeout=timeout,
        retries=retries,
    )
    if status != 200 or not isinstance(payload, dict):
        raise _remote_error("Remote job fetch failed", status, payload)
    return payload


def submit_process_remote(
    base_url: str,
    process_name: str,
    *,
    by_id: bool = False,
    job_id: str | None = None,
    token: str | None = None,
    timeout: float = 10.0,
    retries: int = 2,
) -> dict[str, Any]:
    """Prepare and submit a process via the deferred plans HTTP API."""
    prepare_body: dict[str, Any] = {"process_name": process_name, "by_id": by_id}
    if job_id is not None:
        prepare_body["job_id"] = job_id
    status, prepared = _request_with_retry(
        base_url,
        "POST",
        "/v1/plans/prepare",
        body=prepare_body,
        token=token,
        timeout=timeout,
        retries=retries,
    )
    if status not in {200, 201} or not isinstance(prepared, dict):
        raise _remote_error("Remote process prepare failed", status, prepared)
    plans = prepared.get("plans") or []
    if not plans:
        raise _remote_error("Remote process prepare returned no plans", status, prepared)
    plan_ids = [item["plan_id"] for item in plans if isinstance(item, dict) and item.get("plan_id")]
    if not plan_ids:
        raise _remote_error("Remote process prepare missing plan ids", status, prepared)

    status, submitted = _request_with_retry(
        base_url,
        "POST",
        "/v1/plans/submit",
        body={"plan_ids": plan_ids},
        token=token,
        timeout=timeout,
        retries=retries,
    )
    if status not in {200, 202} or not isinstance(submitted, dict):
        raise _remote_error("Remote process submit failed", status, submitted)
    jobs = submitted.get("jobs") or []
    if not jobs:
        raise _remote_error("Remote process submit returned no jobs", status, submitted)
    first = jobs[0] if isinstance(jobs[0], dict) else {"job_id": jobs[0]}
    result = dict(first)
    result["jobs"] = jobs
    return result


def wait_for_job_remote(
    base_url: str,
    job_id: str,
    *,
    token: str | None = None,
    timeout: float = 10.0,
    poll_interval: float = 0.05,
    retries: int = 2,
    wait_mode: WaitMode = WaitMode.UNTIL_TERMINAL,
) -> dict[str, Any]:
    """Poll remote job status until the configured wait policy is satisfied."""
    deadline = time.monotonic() + timeout
    last: dict[str, Any] = {"job_id": job_id, "status": "unknown"}
    while time.monotonic() < deadline:
        last = get_job_remote(
            base_url,
            job_id,
            token=token,
            timeout=timeout,
            retries=retries,
        )
        if _remote_job_ready(last, wait_mode):
            return last
        time.sleep(poll_interval)
    raise PalmTimeoutError(_format_remote_wait_timeout(job_id, last, wait_mode, timeout))


def _remote_job_ready(payload: dict[str, Any], wait_mode: WaitMode) -> bool:
    status = str(payload.get("status", "")).upper()
    if wait_mode == WaitMode.FIRE_AND_FORGET:
        return True
    if wait_mode == WaitMode.UNTIL_INPUT:
        return status in {
            JobStatus.SUCCEEDED.value,
            JobStatus.FAILED.value,
            JobStatus.CANCELLED.value,
            JobStatus.WAITING_FOR_INPUT.value,
        }
    return status in {
        JobStatus.SUCCEEDED.value,
        JobStatus.FAILED.value,
        JobStatus.CANCELLED.value,
    }


def _format_remote_wait_timeout(
    job_id: str,
    payload: dict[str, Any],
    wait_mode: WaitMode,
    timeout: float,
) -> str:
    status = str(payload.get("status", "unknown")).upper()
    base = (
        f"Timed out after {timeout:g}s waiting for remote job {job_id!r} "
        f"(wait_mode={wait_mode.value}, current status={status})"
    )
    if wait_mode == WaitMode.UNTIL_TERMINAL and status == JobStatus.WAITING_FOR_INPUT.value:
        return (
            f"{base}. The child flow is waiting for interactive input. "
            "Use wait_mode='until_input' on the resource step to return control "
            "to the parent wizard with the child job_id and instance_id."
        )
    if wait_mode == WaitMode.UNTIL_INPUT and status == JobStatus.RUNNING.value:
        return (
            f"{base}. The child job has not reached WAITING_FOR_INPUT yet; "
            "increase timeout_seconds or verify the child flow exposes an interactive step."
        )
    return base


def _transport_error(method: str, path: str, exc: Exception) -> PalmRemoteError:
    return PalmRemoteError(
        f"Remote transport error for {method} {path}: {exc}",
        transient=True,
    )


def _remote_error(
    message: str,
    status: int,
    payload: dict[str, Any] | str,
) -> PalmRemoteError:
    return PalmRemoteError(
        f"{message} ({status}): {payload}",
        status_code=status,
        payload=payload,
        transient=status in _TRANSIENT_STATUS,
    )