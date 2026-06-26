"""Phase 4 REST tests — cancel job, doctor, validate flow."""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from typing import Any

import pytest

from palm.core.orchestration import JobStatus
from palm.definitions import FlowDefinition
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
    subject: str = "dev",
) -> tuple[int, dict[str, Any]]:
    data = None
    headers = {"Accept": "application/json", "X-Palm-Subject": subject}
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


def _wizard_flow() -> FlowDefinition:
    return FlowDefinition(
        name="phase4-wizard",
        pattern="wizard",
        options={
            "steps": [
                {"slug": "name", "title": "Name", "prompt": "Name?"},
            ],
        },
    )


def test_doctor_endpoint(server: ServerRuntime) -> None:
    status, payload = _request(server.base_url, "GET", "/v1/doctor")
    assert status == 200
    assert payload["status"] in {"ok", "degraded"}
    assert "patterns" in payload["registries"]


def test_validate_flow_endpoint(server: ServerRuntime) -> None:
    server.repository.save_flow(_wizard_flow())
    status, payload = _request(
        server.base_url,
        "POST",
        "/v1/flows/validate",
        body={"flow_name": "phase4-wizard"},
    )
    assert status == 200
    assert payload["valid"] is True
    assert payload["pattern"] == "wizard"
    assert payload["step_slugs"] == ["name"]


def test_cancel_job_endpoint(server: ServerRuntime) -> None:
    server.repository.save_flow(_wizard_flow())
    submit_status, submit_payload = _request(
        server.base_url,
        "POST",
        "/v1/jobs",
        body={"flow_name": "phase4-wizard"},
    )
    assert submit_status == 202
    job_id = str(submit_payload["job_id"])

    status, payload = _request(
        server.base_url,
        "POST",
        f"/v1/jobs/{job_id}/cancel",
    )
    assert status == 200
    assert payload["cancelled"] is True
    assert payload["status"] == JobStatus.CANCELLED.value