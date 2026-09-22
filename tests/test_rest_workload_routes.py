"""Workload execution REST routes + HTTP integration (0.56 small surface)."""

from __future__ import annotations

import json
import sys
import urllib.error
import urllib.request
from typing import Any

import pytest

from bundles.standard.runtimes.server import ServerRuntime
from bundles.standard.runtimes.server.surfaces.rest.execution.workloads.routes import ROUTES


def test_workload_routes_registered() -> None:
    paths = {(entry.method, entry.path) for entry in ROUTES}
    assert ("POST", "/v1/api/workloads") in paths
    assert ("GET", "/v1/api/workloads") in paths
    assert ("GET", "/v1/api/workloads/runtimes") in paths
    assert ("GET", "/v1/api/workloads/doctor") in paths
    assert ("GET", "/v1/api/workloads/{workload_id}") in paths
    assert ("POST", "/v1/api/workloads/{workload_id}/stop") in paths
    assert ("POST", "/v1/api/workloads/{workload_id}/exec") in paths


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
        payload = exc.read().decode("utf-8")
        try:
            return exc.code, json.loads(payload)
        except json.JSONDecodeError:
            return exc.code, {"raw": payload}


def test_workload_doctor_and_runtimes_http(server: ServerRuntime) -> None:
    status, doctor = _request(server.base_url, "GET", "/v1/api/workloads/doctor")
    assert status == 200
    assert doctor.get("engine_initialized") is True
    assert doctor.get("default_runtime") == "local"

    status, runtimes = _request(server.base_url, "GET", "/v1/api/workloads/runtimes")
    assert status == 200
    names = {r["name"] for r in runtimes.get("runtimes") or []}
    assert "local" in names
    assert "host" in names
    assert "neonroot" in names


def test_start_local_run_via_rest(server: ServerRuntime) -> None:
    status, body = _request(
        server.base_url,
        "POST",
        "/v1/api/workloads",
        body={
            "spec": {
                "kind": "run",
                "isolation": "best_effort",
                "lifecycle": "job",
                "command": [sys.executable, "-c", "print('rest-ok')"],
                "placement": {"runtime": "local"},
            },
            "owner": {"job_id": "rest-wl"},
        },
    )
    assert status == 201
    assert body.get("status") == "STOPPED"
    assert body.get("result", {}).get("exit_code") == 0
    wid = body["workload_id"]

    status, got = _request(server.base_url, "GET", f"/v1/api/workloads/{wid}")
    assert status == 200
    assert got["workload_id"] == wid

    status, listed = _request(
        server.base_url,
        "GET",
        "/v1/api/workloads?job_id=rest-wl",
    )
    assert status == 200
    assert any(row["workload_id"] == wid for row in listed.get("workloads") or [])
