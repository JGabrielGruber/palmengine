"""Tests for extensible server surfaces, transport, and REST improvements."""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from typing import Any

import pytest

from palm.common.runtimes.server.app import create_server_app
from palm.common.runtimes.server.context import ServerContext
from palm.common.runtimes.server.registry import RouteRegistry, SurfaceRegistry
from palm.common.runtimes.server.transport import transport_registry
from palm.runtimes.server import ServerRuntime, create_app, create_transport
from palm.runtimes.server.surfaces import RestSurface, default_surfaces
from palm.runtimes.server.transport import DEFAULT_TRANSPORT, StdlibHttpTransport


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


def test_surface_registry_lists_default_surfaces(server: ServerRuntime) -> None:
    app = server.server_app
    assert app is not None
    names = app.surfaces.names()
    assert "rest" in names
    assert "websocket" in names
    assert "mcp" in names
    assert "explorer" in names
    assert "studio" in names


def test_health_reports_runtime_and_surfaces(server: ServerRuntime) -> None:
    status, payload = _request(server.base_url, "GET", "/health")
    assert status == 200
    assert payload["runtime"] == "ServerRuntime"
    assert payload["status"] == "ok"
    assert set(payload["surfaces"]) == {"rest", "websocket", "mcp", "explorer", "studio"}


def test_extension_surface_info_endpoints(server: ServerRuntime) -> None:
    for path in ("/v1/surfaces/websocket", "/v1/surfaces/mcp"):
        status, payload = _request(server.base_url, "GET", path)
        assert status == 501
        assert payload["status"] == "planned"
        assert "message" in payload

    status, payload = _request(server.base_url, "GET", "/v1/surfaces/explorer")
    assert status == 200
    assert payload["status"] == "active"
    assert payload["home"] == "/explorer"
    assert payload["explorer"] == "/explorer"


def test_openapi_document(server: ServerRuntime) -> None:
    status, payload = _request(server.base_url, "GET", "/v1/openapi.json")
    assert status == 200
    assert payload["openapi"] == "3.0.3"
    assert "/v1/jobs" in payload["paths"]
    assert any(tag["name"] == "Jobs" for tag in payload["tags"])


def test_list_jobs_pagination_envelope(server: ServerRuntime) -> None:
    status, payload = _request(server.base_url, "GET", "/v1/jobs?limit=10&offset=0")
    assert status == 200
    assert "jobs" in payload
    assert payload["pagination"]["limit"] == 10
    assert payload["pagination"]["offset"] == 0


def test_invalid_pagination_returns_structured_error(server: ServerRuntime) -> None:
    status, payload = _request(server.base_url, "GET", "/v1/jobs?limit=not-a-number")
    assert status == 400
    assert payload["error"] == "invalid_request"
    assert payload["message"] == payload["detail"]
    assert payload["details"][0]["field"] == "limit"


def test_transport_registry_includes_stdlib() -> None:
    assert DEFAULT_TRANSPORT in transport_registry.names()


def test_create_transport_returns_stdlib_binding(server: ServerRuntime) -> None:
    app = server.server_app
    assert app is not None
    transport = create_transport("stdlib", app, host="127.0.0.1", port=0)
    assert isinstance(transport, StdlibHttpTransport)
    assert transport.name == "stdlib"


def test_route_registry_registers_custom_surface() -> None:
    registry = RouteRegistry()
    surfaces = SurfaceRegistry()
    ctx = ServerContext(ServerRuntime())
    rest = RestSurface(ctx, surface_names=["rest"])
    surfaces.register(rest)
    rest.register(registry)
    assert registry.match("GET", "/v1/jobs") is not None
    assert registry.match("GET", "/v1/instances") is not None


def test_create_server_app_with_explicit_rest_surface(server: ServerRuntime) -> None:
    ctx = ServerContext(server, plan_registry=server.plan_registry)
    app = create_server_app(ctx, surfaces=[RestSurface(ctx, surface_names=["rest"])])
    assert app.surfaces.names() == ["rest"]
    assert app.routes.match("GET", "/health") is not None


def test_create_app_mounts_default_surfaces(server: ServerRuntime) -> None:
    app = create_app(server)
    assert set(app.surfaces.names()) == {"rest", "websocket", "mcp", "explorer", "studio"}
    assert len(default_surfaces(ServerContext(server))) == 5
