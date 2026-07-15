"""Integration tests for ``/v1/api`` command-path REST routes."""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from typing import Any

import pytest

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


def test_list_definitions_flows_under_api_prefix(server: ServerRuntime) -> None:
    status, body = _request(server.base_url, "GET", "/v1/api/definitions/flows")
    assert status == 200
    assert isinstance(body, dict)
    assert "flows" in body


def test_list_execution_flows_under_api_prefix(server: ServerRuntime) -> None:
    status, body = _request(server.base_url, "GET", "/v1/api/flows")
    assert status == 200
    assert isinstance(body, dict)
    assert "flows" in body


def test_create_flow_session_via_command_path(server: ServerRuntime) -> None:
    status, body = _request(
        server.base_url,
        "POST",
        "/v1/api/flows/onboard/create",
        body={"wizard": {"name": "onboard", "steps": 2}},
    )
    assert status in {200, 202}
    assert isinstance(body, dict)
    assert body.get("session_id")


def test_get_session_context_via_command_path(server: ServerRuntime) -> None:
    status, created = _request(
        server.base_url,
        "POST",
        "/v1/api/flows/onboard/create",
        body={"wizard": {"name": "onboard", "steps": 2}},
    )
    assert status in {200, 202}
    assert isinstance(created, dict)
    session_id = created.get("session_id")
    assert session_id

    status, body = _request(
        server.base_url,
        "GET",
        f"/v1/api/flows/onboard/session/{session_id}",
    )
    assert status == 200
    assert isinstance(body, dict)
    assert body.get("instance_id") == session_id
    assert "next_actions" in body


def test_legacy_instances_path_not_mounted(server: ServerRuntime) -> None:
    status, _body = _request(
        server.base_url,
        "POST",
        "/v1/api/flows/onboard/instances",
        body={"wizard": {"name": "onboard", "steps": 2}},
    )
    assert status == 404