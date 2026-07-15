"""Tests for flow session REST endpoints (0.16 command-path)."""

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
        if "application/json" in exc.headers.get("Content-Type", ""):
            return exc.code, json.loads(raw)
        return exc.code, raw


def _flow_id() -> str:
    return "onboard"


def _create_session(server: ServerRuntime, *, body: dict[str, Any] | None = None) -> dict[str, Any]:
    flow_id = _flow_id()
    status, payload = _request(
        server.base_url,
        "POST",
        f"/v1/api/flows/{flow_id}/create",
        body=body or {"wizard": {"name": flow_id, "steps": 2}},
    )
    assert status in {200, 202}
    assert isinstance(payload, dict)
    return payload


def test_create_session_returns_session_id(server: ServerRuntime) -> None:
    payload = _create_session(server)
    assert payload.get("session_id")
    assert payload.get("job_id")
    assert payload["status"] == JobStatus.WAITING_FOR_INPUT.value


def test_get_session_returns_prompt(server: ServerRuntime) -> None:
    created = _create_session(server)
    session_id = created["session_id"]
    flow_id = _flow_id()

    status, payload = _request(
        server.base_url,
        "GET",
        f"/v1/api/flows/{flow_id}/session/{session_id}",
    )
    assert status == 200
    assert isinstance(payload, dict)
    assert payload.get("session_id") == session_id or payload.get("instance_id") == session_id
    assert payload.get("job_id") == created["job_id"]
    assert payload.get("status") == JobStatus.WAITING_FOR_INPUT.value
    assert payload.get("prompt") is not None or payload.get("current_step_slug") is not None
    assert payload.get("step") is not None


def test_get_session_not_found(server: ServerRuntime) -> None:
    status, payload = _request(
        server.base_url,
        "GET",
        f"/v1/api/flows/{_flow_id()}/session/missing-instance",
    )
    assert status == 404
    assert isinstance(payload, dict)
    assert payload["error"] == "wizard_not_found"


def test_create_session_validation_error(server: ServerRuntime) -> None:
    status, payload = _request(
        server.base_url,
        "POST",
        f"/v1/api/flows/{_flow_id()}/create",
        body={},
    )
    assert status in {400, 500}
    assert isinstance(payload, dict)
    assert payload["error"] in {
        "validation_failed",
        "invalid_request",
        "bad_request",
        "submit_failed",
    }


def test_session_input_advances_step(server: ServerRuntime) -> None:
    created = _create_session(server)
    session_id = created["session_id"]
    flow_id = _flow_id()

    status, payload = _request(
        server.base_url,
        "POST",
        f"/v1/api/flows/{flow_id}/session/{session_id}/input",
        body={"value": "Ada"},
    )
    assert status == 200
    assert isinstance(payload, dict)
    assert payload.get("session_id") == session_id or payload.get("instance_id") == session_id
    assert payload.get("step") is not None
    assert payload.get("status") in {
        JobStatus.WAITING_FOR_INPUT.value,
        JobStatus.SUCCEEDED.value,
    }
    assert payload.get("prompt") is not None or payload.get("current_step_slug") is not None
    next_actions = payload.get("next_actions") or []
    # compact/powertool view returns next_actions as a list of action-name strings
    assert all(isinstance(action, str) for action in next_actions)


def test_session_input_not_found(server: ServerRuntime) -> None:
    status, payload = _request(
        server.base_url,
        "POST",
        f"/v1/api/flows/{_flow_id()}/session/missing-instance/input",
        body={"value": "Ada"},
    )
    assert status == 404
    assert isinstance(payload, dict)
    assert payload["error"] == "wizard_not_found"


def test_session_backtrack_returns_to_previous_step(server: ServerRuntime) -> None:
    created = _create_session(server)
    session_id = created["session_id"]
    flow_id = _flow_id()

    status, after_input = _request(
        server.base_url,
        "POST",
        f"/v1/api/flows/{flow_id}/session/{session_id}/input",
        body={"value": "Ada"},
    )
    assert status == 200
    assert isinstance(after_input, dict)

    status, payload = _request(
        server.base_url,
        "POST",
        f"/v1/api/flows/{flow_id}/session/{session_id}/backtrack",
        body={},
    )
    assert status == 200
    assert isinstance(payload, dict)
    assert payload["step"] == "step_1"
    assert payload["status"] == JobStatus.WAITING_FOR_INPUT.value
    assert payload.get("prompt") is not None


def test_session_backtrack_rejects_first_step(server: ServerRuntime) -> None:
    created = _create_session(server)
    session_id = created["session_id"]
    flow_id = _flow_id()

    status, payload = _request(
        server.base_url,
        "POST",
        f"/v1/api/flows/{flow_id}/session/{session_id}/backtrack",
        body={},
    )
    assert status == 400
    assert isinstance(payload, dict)
    assert payload["error"] == "backtrack_rejected"


def test_session_backtrack_explicit_target(server: ServerRuntime) -> None:
    created = _create_session(server)
    session_id = created["session_id"]
    flow_id = _flow_id()

    _request(
        server.base_url,
        "POST",
        f"/v1/api/flows/{flow_id}/session/{session_id}/input",
        body={"value": "Ada"},
    )
    status, payload = _request(
        server.base_url,
        "POST",
        f"/v1/api/flows/{flow_id}/session/{session_id}/backtrack",
        body={"to_step": "step_1"},
    )
    assert status == 200
    assert isinstance(payload, dict)
    assert payload["step"] == "step_1"