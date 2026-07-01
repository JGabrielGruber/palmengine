"""Integration tests for ``/v1/api/system`` REST routes."""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from typing import Any

import pytest

from palm.core.orchestration import JobStatus
from palm.runtimes.server import ServerRuntime


@pytest.fixture
def server() -> ServerRuntime:
    rt = ServerRuntime(host="127.0.0.1", port=0)
    rt.start(port=0)
    yield rt
    rt.stop()


def _request(
    base_url: str,
    method: str,
    path: str,
    *,
    body: dict[str, Any] | None = None,
) -> tuple[int, dict[str, Any] | str]:
    data = None
    headers = {"Accept": "application/json"}
    if body is not None:
        data = json.dumps(body).encode("utf-8")
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(
        f"{base_url}{path}",
        data=data,
        headers=headers,
        method=method,
    )
    try:
        with urllib.request.urlopen(req, timeout=5) as resp:
            raw = resp.read().decode("utf-8")
            if "application/json" in resp.headers.get("Content-Type", ""):
                return resp.status, json.loads(raw)
            return resp.status, raw
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode("utf-8")
        try:
            return exc.code, json.loads(raw)
        except json.JSONDecodeError:
            return exc.code, raw


def test_system_job_context_after_flow_create(server: ServerRuntime) -> None:
    status, created = _request(
        server.base_url,
        "POST",
        "/v1/api/flows/onboard/create",
        body={"wizard": {"name": "onboard", "steps": 2}},
    )
    assert status in {200, 202}
    assert isinstance(created, dict)
    job_id = created.get("job_id")
    assert job_id

    status, context = _request(
        server.base_url,
        "GET",
        f"/v1/api/system/jobs/{job_id}/context",
    )
    assert status == 200
    assert isinstance(context, dict)
    assert context["found"] is True
    assert context["job_id"] == job_id
    assert context["status"] == JobStatus.WAITING_FOR_INPUT.value
    assert context["instance"]["link"].startswith("/v1/api/system/instances/")
    assert any(
        item["action"] == "provide_input"
        and "/v1/api/flows/" in item["path"]
        for item in context.get("next_actions") or []
    )


def test_legacy_jobs_path_not_mounted(server: ServerRuntime) -> None:
    status, _body = _request(server.base_url, "GET", "/v1/jobs")
    assert status == 404