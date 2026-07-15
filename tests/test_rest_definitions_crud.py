"""Tests for definitions catalog CRUD under /v1/api/definitions."""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from typing import Any

import pytest

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
) -> tuple[int, dict[str, Any] | str]:
    data = None
    headers = {"Accept": "application/json", "X-Palm-Subject": "dev"}
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
            return exc.code, {"error": raw}


def test_create_and_delete_flow(server: ServerRuntime) -> None:
    flow_body = {
        "name": "crud-flow",
        "pattern": "wizard",
        "options": {"steps": [{"slug": "one", "title": "One", "prompt": "One?"}]},
    }
    status, created = _request(
        server.base_url,
        "POST",
        "/v1/api/definitions/flows",
        body=flow_body,
    )
    assert status == 201
    assert isinstance(created, dict)
    assert created["saved"] is True
    assert created["flow"]["name"] == "crud-flow"

    status, fetched = _request(server.base_url, "GET", "/v1/api/definitions/flows/crud-flow")
    assert status == 200
    assert isinstance(fetched, dict)
    assert fetched["name"] == "crud-flow"

    status, deleted = _request(
        server.base_url,
        "DELETE",
        "/v1/api/definitions/flows/crud-flow",
    )
    assert status == 200
    assert isinstance(deleted, dict)
    assert deleted["deleted"] is True

    status, _missing = _request(server.base_url, "GET", "/v1/api/definitions/flows/crud-flow")
    assert status == 404


def test_update_flow(server: ServerRuntime) -> None:
    server.repository.register_flow(
        FlowDefinition(name="patch-flow", pattern="wizard", options={"steps": []}),
    )
    status, updated = _request(
        server.base_url,
        "PUT",
        "/v1/api/definitions/flows/patch-flow",
        body={
            "name": "patch-flow",
            "pattern": "wizard",
            "options": {"steps": [{"slug": "x", "title": "X", "prompt": "X?"}]},
        },
    )
    assert status == 200
    assert isinstance(updated, dict)
    assert updated["flow"]["options"]["steps"][0]["slug"] == "x"


def test_create_and_delete_resource(server: ServerRuntime, rest_base_url: str) -> None:
    resource_body = {
        "name": "crud-echo",
        "provider": "rest",
        "action": "fetch",
        "resource_id": "echo",
        "params": {"base_url": rest_base_url},
    }
    status, created = _request(
        server.base_url,
        "POST",
        "/v1/api/definitions/resources",
        body=resource_body,
    )
    assert status == 201
    assert isinstance(created, dict)
    assert created["resource"]["name"] == "crud-echo"

    status, deleted = _request(
        server.base_url,
        "DELETE",
        "/v1/api/definitions/resources/crud-echo",
    )
    assert status == 200
    assert deleted["deleted"] is True