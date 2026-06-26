"""Bridge Palm's stdlib HTTP transport to FastMCP streamable-http and SSE."""

from __future__ import annotations

import json
import threading
from typing import TYPE_CHECKING, Any

from palm.common.runtimes.server.middleware import PALM_SUBJECT_HEADER
from palm.common.runtimes.server.protocol import ServerRequest, ServerResponse
from palm.runtimes.mcp.config import PalmMcpConfig

if TYPE_CHECKING:
    from starlette.testclient import TestClient


_lock = threading.RLock()
_bridges: dict[str, McpHttpBridge] = {}


class McpHttpBridge:
    """Serve FastMCP HTTP transports via a Starlette test client."""

    def __init__(self, *, base_url: str, starlette_app: Any) -> None:
        self._base_url = base_url
        self._starlette_app = starlette_app
        self._client: TestClient | None = None

    @property
    def base_url(self) -> str:
        return self._base_url

    def start(self) -> None:
        if self._client is not None:
            return
        from starlette.testclient import TestClient

        self._client = TestClient(self._starlette_app)
        self._client.__enter__()

    def stop(self) -> None:
        client = self._client
        if client is None:
            return
        client.__exit__(None, None, None)
        self._client = None

    def dispatch(self, request: ServerRequest) -> ServerResponse:
        client = self._client
        if client is None:
            return ServerResponse(
                status=503,
                body={"error": "mcp_unavailable", "message": "MCP HTTP bridge is not started"},
            )

        headers = {key: value for key, value in request.headers.items()}
        data = None
        if request.body is not None:
            data = json.dumps(request.body).encode("utf-8")
            headers.setdefault("Content-Type", "application/json")

        response = client.request(
            request.method,
            request.path,
            headers=headers,
            content=data,
        )
        content_type = response.headers.get("content-type", "application/json")
        return ServerResponse(
            status=response.status_code,
            headers={
                key: value
                for key, value in response.headers.items()
                if key.lower() not in {"content-length", "content-type"}
            },
            content_type=content_type,
            raw_body=response.content,
        )


def build_mcp_starlette_app(mcp_server: Any) -> Any:
    """Combine streamable-http (``/mcp``) and SSE (``/mcp/sse``, ``/mcp/messages``) apps."""
    from fastmcp.server.http import create_sse_app, create_streamable_http_app
    from starlette.applications import Starlette

    streamable = create_streamable_http_app(
        mcp_server,
        streamable_http_path="/mcp",
    )
    sse = create_sse_app(
        mcp_server,
        sse_path="/mcp/sse",
        message_path="/mcp/messages",
    )
    return Starlette(
        routes=[*streamable.routes, *sse.routes],
        lifespan=streamable.lifespan,
    )


def get_mcp_http_bridge(base_url: str, *, subject: str = "dev") -> McpHttpBridge | None:
    """Return a started MCP HTTP bridge for ``base_url``, creating it on first use."""
    normalized = base_url.rstrip("/")
    cache_key = f"{normalized}|{subject}"
    with _lock:
        existing = _bridges.get(cache_key)
        if existing is not None:
            return existing

        try:
            import fastmcp  # noqa: F401
        except ImportError:
            return None

        from palm.runtimes.mcp.server import create_mcp_server

        env_config = PalmMcpConfig.from_env()
        config = PalmMcpConfig(
            base_url=normalized,
            subject=subject,
            llms_txt_path=env_config.llms_txt_path,
        )
        mcp_server = create_mcp_server(config)
        starlette_app = build_mcp_starlette_app(mcp_server)
        bridge = McpHttpBridge(base_url=normalized, starlette_app=starlette_app)
        bridge.start()
        _bridges[cache_key] = bridge
        return bridge


def shutdown_mcp_http_bridges() -> None:
    """Stop all active MCP HTTP bridges (called when the server transport stops)."""
    with _lock:
        bridges = list(_bridges.values())
        _bridges.clear()
    for bridge in bridges:
        bridge.stop()


def mcp_http_available() -> bool:
    """Return whether the optional ``mcp`` extra is installed."""
    try:
        import fastmcp  # noqa: F401
    except ImportError:
        return False
    return True


def subject_from_request(request: ServerRequest, *, default: str = "dev") -> str:
    """Resolve ``X-Palm-Subject`` for loopback REST calls from MCP HTTP requests."""
    for key, value in request.headers.items():
        if key.lower() == PALM_SUBJECT_HEADER.lower():
            stripped = str(value).strip()
            if stripped:
                return stripped
    return default


__all__ = [
    "McpHttpBridge",
    "build_mcp_starlette_app",
    "get_mcp_http_bridge",
    "mcp_http_available",
    "shutdown_mcp_http_bridges",
    "subject_from_request",
]