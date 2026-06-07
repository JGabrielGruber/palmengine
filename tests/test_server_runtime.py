"""Tests for ServerRuntime HTTP surface."""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from typing import Any

import pytest

from palm.core.orchestration import JobStatus
from palm.runtimes.host import RuntimeHost
from palm.runtimes.schedulers import QueuedScheduler
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
        with urllib.request.urlopen(req, timeout=5) as resp:
            payload = json.loads(resp.read().decode("utf-8"))
            return resp.status, payload
    except urllib.error.HTTPError as exc:
        payload = json.loads(exc.read().decode("utf-8"))
        return exc.code, payload


def test_server_runtime_satisfies_runtime_host() -> None:
    rt = ServerRuntime()
    assert isinstance(rt, RuntimeHost)


def test_server_defaults_to_queued_scheduler(server: ServerRuntime) -> None:
    assert isinstance(server.orchestration.scheduler, QueuedScheduler)


def test_health_endpoint(server: ServerRuntime) -> None:
    status, payload = _request(server.base_url, "GET", "/health")
    assert status == 200
    assert payload["status"] == "ok"
    assert payload["runtime"] == "ServerRuntime"


def test_submit_wizard_and_provide_input(server: ServerRuntime) -> None:
    status, payload = _request(
        server.base_url,
        "POST",
        "/v1/jobs",
        body={"wizard": {"name": "onboard", "steps": 2}},
    )
    assert status == 202
    job_id = payload["job_id"]
    assert payload["status"] == JobStatus.WAITING_FOR_INPUT.value

    status, job_payload = _request(server.base_url, "GET", f"/v1/jobs/{job_id}")
    assert status == 200
    assert job_payload["status"] == JobStatus.WAITING_FOR_INPUT.value

    status, input_payload = _request(
        server.base_url,
        "POST",
        f"/v1/jobs/{job_id}/input",
        body={"value": "Ada"},
    )
    assert status == 200
    assert input_payload["status"] in {
        JobStatus.WAITING_FOR_INPUT.value,
        JobStatus.SUCCEEDED.value,
    }

    server.wait_until_idle()
    job = server.get_job(job_id)
    assert job.status in {JobStatus.WAITING_FOR_INPUT, JobStatus.SUCCEEDED}