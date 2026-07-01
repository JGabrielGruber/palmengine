"""Tests for process execution REST route registration and HTTP integration."""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from typing import Any

import pytest

from palm.core.orchestration import JobStatus
from palm.runtimes.server import ServerRuntime
from palm.runtimes.server.surfaces.rest.execution.processes.routes import ROUTES


def test_process_routes_registered() -> None:
    paths = {(entry.method, entry.path) for entry in ROUTES}
    assert ("POST", "/v1/api/processes/{process_id}/prepare") in paths
    assert ("POST", "/v1/api/processes/submit") in paths
    assert ("POST", "/v1/api/processes/{process_id}/run") in paths


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
) -> tuple[int, dict[str, Any]]:
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
        with urllib.request.urlopen(req, timeout=10) as resp:
            return resp.status, json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        return exc.code, json.loads(exc.read().decode("utf-8"))


def test_prepare_and_submit_process_http(server: ServerRuntime) -> None:
    status, prepared = _request(
        server.base_url,
        "POST",
        "/v1/api/processes/pipeline/prepare",
        body={
            "process": {
                "name": "pipeline",
                "flows": [
                    {"name": "extract", "pattern": "etl"},
                    {"name": "graph", "pattern": "dag"},
                ],
            }
        },
    )
    assert status == 201
    assert len(prepared["plans"]) == 2
    plan_ids = [item["plan_id"] for item in prepared["plans"]]

    status, submitted = _request(
        server.base_url,
        "POST",
        "/v1/api/processes/submit",
        body={"plan_ids": plan_ids},
    )
    assert status == 202
    assert len(submitted["jobs"]) == 2
    assert submitted["jobs"][0]["status"] == JobStatus.SUCCEEDED.value


def test_legacy_plans_path_not_mounted(server: ServerRuntime) -> None:
    status, _payload = _request(
        server.base_url,
        "POST",
        "/v1/plans/prepare",
        body={"process_name": "pipeline"},
    )
    assert status == 404