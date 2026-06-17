"""Tests for extensible server surfaces and registry."""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from typing import Any

import pytest

from palm.common.runtimes.server.app import create_server_app
from palm.common.runtimes.server.context import ServerContext
from palm.common.runtimes.server.registry import RouteRegistry, SurfaceRegistry
from palm.common.runtimes.server.surfaces.rest import RestSurface
from palm.runtimes.server import ServerRuntime


@pytest.fixture
def server() -> ServerRuntime:
    rt = ServerRuntime(host="127.0.0.1", port=0)
    rt.start(port=0)
    yield rt
    rt.stop()


def _request(base_url: str, method: str, path: str) -> tuple[int, dict[str, Any]]:
    req = urllib.request.Request(
        f"{base_url}{path}",
        headers={"Accept": "application/json"},
        method=method,
    )
    try:
        with urllib.request.urlopen(req, timeout=5) as resp:
            payload = json.loads(resp.read().decode("utf-8"))
            return resp.status, payload
    except urllib.error.HTTPError as exc:
        payload = json.loads(exc.read().decode("utf-8"))
        return exc.code, payload


def test_surface_registry_lists_default_surfaces(server: ServerRuntime) -> None:
    app = server.server_app
    assert app is not None
    names = app.surfaces.names()
    assert "rest" in names
    assert "websocket" in names
    assert "mcp" in names
    assert "ssr" in names


def test_health_reports_runtime_and_surfaces(server: ServerRuntime) -> None:
    status, payload = _request(server.base_url, "GET", "/health")
    assert status == 200
    assert payload["runtime"] == "ServerRuntime"
    assert payload["status"] == "ok"


def test_extension_surface_info_endpoints(server: ServerRuntime) -> None:
    for path in ("/v1/surfaces/websocket", "/v1/surfaces/mcp", "/v1/surfaces/ssr"):
        status, payload = _request(server.base_url, "GET", path)
        assert status == 501
        assert payload["status"] == "planned"


def test_route_registry_registers_custom_surface() -> None:
    registry = RouteRegistry()
    surfaces = SurfaceRegistry()
    ctx = ServerContext(ServerRuntime())
    rest = RestSurface(ctx)
    surfaces.register(rest)
    rest.register(registry)
    assert registry.match("GET", "/v1/jobs") is not None
    assert registry.match("GET", "/v1/instances") is not None


def test_create_server_app_with_explicit_rest_surface(server: ServerRuntime) -> None:
    ctx = ServerContext(server, plan_registry=server.plan_registry)
    app = create_server_app(ctx, surfaces=[RestSurface(ctx)], include_defaults=False)
    assert app.surfaces.names() == ["rest"]
    assert app.routes.match("GET", "/health") is not None