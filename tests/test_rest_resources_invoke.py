"""Tests for POST /v1/resources/invoke REST endpoint."""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from typing import Any

import pytest

from palm.definitions import ResourceDefinition
from palm.runtimes.server import ServerRuntime


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
            return exc.code, {"error": raw}


@pytest.fixture
def server(rest_base_url: str) -> ServerRuntime:
    rt = ServerRuntime(host="127.0.0.1", port=0)
    rt.start(port=0)
    rt.repository.save_resource(
        ResourceDefinition(
            id="resource-rest-echo",
            name="rest-echo",
            provider="rest",
            action="fetch",
            resource_id="echo",
            params={"base_url": rest_base_url},
        ),
    )
    yield rt
    rt.stop()


def test_invoke_resource_rest_endpoint(server: ServerRuntime) -> None:
    status, payload = _request(
        server.base_url,
        "POST",
        "/v1/resources/invoke",
        body={"resource_ref": "rest-echo"},
    )
    assert status == 200
    assert isinstance(payload, dict)
    assert payload["success"] is True
    assert payload["data"]["body"]["ok"] is True


def test_invoke_resource_missing_ref(server: ServerRuntime) -> None:
    status, payload = _request(
        server.base_url,
        "POST",
        "/v1/resources/invoke",
        body={},
    )
    assert status == 400
    assert isinstance(payload, dict)
