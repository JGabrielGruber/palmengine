"""Native HTTP MCP surface tests — streamable-http on /mcp."""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from typing import Any

import pytest

fastmcp = pytest.importorskip("fastmcp")

from palm.runtimes.mcp.http_bridge import shutdown_mcp_http_bridges  # noqa: E402
from palm.runtimes.server import ServerRuntime  # noqa: E402


@pytest.fixture
def server() -> ServerRuntime:
    rt = ServerRuntime(host="127.0.0.1", port=0)
    rt.start(port=0)
    yield rt
    rt.stop()
    shutdown_mcp_http_bridges()


def _raw_request(
    base_url: str,
    method: str,
    path: str,
    *,
    body: dict[str, Any] | None = None,
    headers: dict[str, str] | None = None,
) -> tuple[int, dict[str, str], bytes]:
    data = None
    req_headers = {
        "Accept": "application/json, text/event-stream",
        **(headers or {}),
    }
    if body is not None:
        data = json.dumps(body).encode("utf-8")
        req_headers["Content-Type"] = "application/json"
    req = urllib.request.Request(
        f"{base_url}{path}",
        data=data,
        headers=req_headers,
        method=method,
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return resp.status, dict(resp.headers), resp.read()
    except urllib.error.HTTPError as exc:
        return exc.code, dict(exc.headers), exc.read()


def test_mcp_surface_info_reports_active_http(server: ServerRuntime) -> None:
    status, headers, raw = _raw_request(server.base_url, "GET", "/v1/surfaces/mcp")
    assert status == 200
    payload = json.loads(raw.decode("utf-8"))
    assert payload["status"] == "active"
    assert "streamable-http" in payload["transports"]
    assert "sse" in payload["transports"]
    assert payload["endpoint"] == "/mcp"
    http = payload["http"]
    assert http["streamable_http"]["path"] == "/mcp"
    assert http["sse"]["sse_path"] == "/mcp/sse"
    assert http["sse"]["message_path"] == "/mcp/messages"


def test_mcp_http_initialize(server: ServerRuntime) -> None:
    status, headers, raw = _raw_request(
        server.base_url,
        "POST",
        "/mcp",
        body={
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {"name": "pytest", "version": "1"},
            },
        },
    )
    assert status == 200
    assert "text/event-stream" in headers.get("Content-Type", headers.get("content-type", ""))
    text = raw.decode("utf-8")
    assert '"protocolVersion"' in text