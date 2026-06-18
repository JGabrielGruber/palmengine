"""Tests for /v1/wizards REST endpoints."""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from typing import Any

import pytest

from palm.core.orchestration import JobStatus
from palm.runtimes.server import ServerRuntime
from palm.runtimes.server.surfaces.rest.route_table import rest_routes


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


def test_rest_routes_include_wizards_group() -> None:
    groups = {route.group for route in rest_routes()}
    assert "Wizards" in groups
    route_ids = {route.route_id for route in rest_routes()}
    assert {"submit_wizard", "get_wizard", "provide_wizard_input", "backtrack_wizard"} <= route_ids


def test_submit_wizard_returns_instance_id(server: ServerRuntime) -> None:
    status, payload = _request(
        server.base_url,
        "POST",
        "/v1/wizards",
        body={"wizard": {"name": "onboard", "steps": 2}},
    )
    assert status == 202
    assert isinstance(payload, dict)
    assert "instance_id" in payload
    assert "job_id" in payload
    assert payload["status"] == JobStatus.WAITING_FOR_INPUT.value


def test_get_wizard_returns_prompt(server: ServerRuntime) -> None:
    status, created = _request(
        server.base_url,
        "POST",
        "/v1/wizards",
        body={"wizard": {"name": "onboard", "steps": 2}},
    )
    assert status == 202
    assert isinstance(created, dict)
    instance_id = created["instance_id"]

    status, payload = _request(server.base_url, "GET", f"/v1/wizards/{instance_id}")
    assert status == 200
    assert isinstance(payload, dict)
    assert payload["instance_id"] == instance_id
    assert payload["job_id"] == created["job_id"]
    assert payload["status"] == JobStatus.WAITING_FOR_INPUT.value
    assert payload.get("prompt") is not None or payload.get("wizard_step_slug") is not None
    assert payload["links"]["self"] == f"/v1/wizards/{instance_id}"


def test_get_wizard_not_found(server: ServerRuntime) -> None:
    status, payload = _request(server.base_url, "GET", "/v1/wizards/missing-instance")
    assert status == 404
    assert isinstance(payload, dict)
    assert payload["error"] == "wizard_not_found"


def test_submit_wizard_validation_error(server: ServerRuntime) -> None:
    status, payload = _request(server.base_url, "POST", "/v1/wizards", body={})
    assert status == 400
    assert isinstance(payload, dict)
    assert payload["error"] in {"validation_failed", "invalid_request"}


def _start_wizard(server: ServerRuntime) -> dict[str, Any]:
    status, payload = _request(
        server.base_url,
        "POST",
        "/v1/wizards",
        body={"wizard": {"name": "onboard", "steps": 2}},
    )
    assert status == 202
    assert isinstance(payload, dict)
    return payload


def test_provide_wizard_input_advances_step(server: ServerRuntime) -> None:
    created = _start_wizard(server)
    instance_id = created["instance_id"]

    status, payload = _request(
        server.base_url,
        "POST",
        f"/v1/wizards/{instance_id}/input",
        body={"value": "Ada"},
    )
    assert status == 200
    assert isinstance(payload, dict)
    assert payload["instance_id"] == instance_id
    assert payload["slug"] is not None
    assert payload["status"] in {
        JobStatus.WAITING_FOR_INPUT.value,
        JobStatus.SUCCEEDED.value,
    }
    assert payload.get("prompt") is not None or payload.get("wizard_step_slug") is not None
    next_actions = payload.get("next_actions") or []
    assert any(action["path"] == f"/v1/wizards/{instance_id}/input" for action in next_actions)


def test_provide_wizard_input_not_found(server: ServerRuntime) -> None:
    status, payload = _request(
        server.base_url,
        "POST",
        "/v1/wizards/missing-instance/input",
        body={"value": "Ada"},
    )
    assert status == 404
    assert isinstance(payload, dict)
    assert payload["error"] == "wizard_not_found"


def test_backtrack_wizard_returns_to_previous_step(server: ServerRuntime) -> None:
    created = _start_wizard(server)
    instance_id = created["instance_id"]

    status, after_input = _request(
        server.base_url,
        "POST",
        f"/v1/wizards/{instance_id}/input",
        body={"value": "Ada"},
    )
    assert status == 200
    assert isinstance(after_input, dict)

    status, payload = _request(
        server.base_url,
        "POST",
        f"/v1/wizards/{instance_id}/backtrack",
        body={},
    )
    assert status == 200
    assert isinstance(payload, dict)
    assert payload["to_step"] == "step_1"
    assert payload["status"] == JobStatus.WAITING_FOR_INPUT.value
    assert payload.get("prompt", {}).get("step") == "step_1" or payload.get("wizard_step_slug") == "step_1"


def test_backtrack_wizard_rejects_first_step(server: ServerRuntime) -> None:
    created = _start_wizard(server)
    instance_id = created["instance_id"]

    status, payload = _request(
        server.base_url,
        "POST",
        f"/v1/wizards/{instance_id}/backtrack",
        body={},
    )
    assert status == 400
    assert isinstance(payload, dict)
    assert payload["error"] == "backtrack_rejected"


def test_backtrack_wizard_explicit_target(server: ServerRuntime) -> None:
    created = _start_wizard(server)
    instance_id = created["instance_id"]

    _request(
        server.base_url,
        "POST",
        f"/v1/wizards/{instance_id}/input",
        body={"value": "Ada"},
    )
    status, payload = _request(
        server.base_url,
        "POST",
        f"/v1/wizards/{instance_id}/backtrack",
        body={"to_step": "step_1"},
    )
    assert status == 200
    assert isinstance(payload, dict)
    assert payload["to_step"] == "step_1"