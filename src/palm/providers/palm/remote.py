"""HTTP client for remote Palm ServerRuntime invocations."""

from __future__ import annotations

import json
import time
import urllib.error
import urllib.request
from typing import Any

from palm.core.orchestration import JobStatus


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


def submit_flow_remote(
    base_url: str,
    flow_name: str,
    *,
    by_id: bool = False,
    job_id: str | None = None,
    token: str | None = None,
    timeout: float = 10.0,
) -> dict[str, Any]:
    """Submit a flow via ``POST /v1/jobs`` and return the acceptance payload."""
    body: dict[str, Any] = {"flow_name": flow_name, "by_id": by_id}
    if job_id is not None:
        body["job_id"] = job_id
    status, payload = _request(
        base_url,
        "POST",
        "/v1/jobs",
        body=body,
        token=token,
        timeout=timeout,
    )
    if status not in {200, 202} or not isinstance(payload, dict):
        raise RuntimeError(f"Remote flow submit failed ({status}): {payload}")
    return payload


def get_job_remote(
    base_url: str,
    job_id: str,
    *,
    token: str | None = None,
    timeout: float = 10.0,
) -> dict[str, Any]:
    """Fetch job status via ``GET /v1/jobs/{job_id}``."""
    status, payload = _request(
        base_url,
        "GET",
        f"/v1/jobs/{job_id}",
        token=token,
        timeout=timeout,
    )
    if status != 200 or not isinstance(payload, dict):
        raise RuntimeError(f"Remote job fetch failed ({status}): {payload}")
    return payload


def submit_process_remote(
    base_url: str,
    process_name: str,
    *,
    by_id: bool = False,
    job_id: str | None = None,
    token: str | None = None,
    timeout: float = 10.0,
) -> dict[str, Any]:
    """Prepare and submit a process via the deferred plans HTTP API."""
    prepare_body: dict[str, Any] = {"process_name": process_name, "by_id": by_id}
    if job_id is not None:
        prepare_body["job_id"] = job_id
    status, prepared = _request(
        base_url,
        "POST",
        "/v1/plans/prepare",
        body=prepare_body,
        token=token,
        timeout=timeout,
    )
    if status not in {200, 201} or not isinstance(prepared, dict):
        raise RuntimeError(f"Remote process prepare failed ({status}): {prepared}")
    plans = prepared.get("plans") or []
    if not plans:
        raise RuntimeError(f"Remote process prepare returned no plans: {prepared}")
    plan_ids = [item["plan_id"] for item in plans if isinstance(item, dict) and item.get("plan_id")]
    if not plan_ids:
        raise RuntimeError(f"Remote process prepare missing plan ids: {prepared}")

    status, submitted = _request(
        base_url,
        "POST",
        "/v1/plans/submit",
        body={"plan_ids": plan_ids},
        token=token,
        timeout=timeout,
    )
    if status not in {200, 202} or not isinstance(submitted, dict):
        raise RuntimeError(f"Remote process submit failed ({status}): {submitted}")
    jobs = submitted.get("jobs") or []
    if not jobs:
        raise RuntimeError(f"Remote process submit returned no jobs: {submitted}")
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
) -> dict[str, Any]:
    """Poll remote job status until terminal or timeout."""
    deadline = time.monotonic() + timeout
    last: dict[str, Any] = {}
    while time.monotonic() < deadline:
        last = get_job_remote(base_url, job_id, token=token, timeout=timeout)
        status = str(last.get("status", "")).upper()
        if status in {
            JobStatus.SUCCEEDED.value,
            JobStatus.FAILED.value,
            JobStatus.CANCELLED.value,
        }:
            return last
        time.sleep(poll_interval)
    raise TimeoutError(f"Timed out waiting for remote job {job_id!r}")