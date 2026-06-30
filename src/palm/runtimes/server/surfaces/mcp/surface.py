"""
MCP surface — stdio adapter discovery and native streamable-http transport.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from palm.common.runtimes.server.protocol import ServerRequest, ServerResponse
from palm.common.runtimes.server.surface import BaseSurface

if TYPE_CHECKING:
    from palm.common.runtimes.server.context import ServerContext
    from palm.common.runtimes.server.registry import RouteRegistry


class McpSurface(BaseSurface):
    """Operator MCP — ``palm-mcp`` stdio adapter and optional ``/mcp`` HTTP transport."""

    def __init__(self, ctx: ServerContext) -> None:
        self._ctx = ctx

    @property
    def name(self) -> str:
        return "mcp"

    @property
    def mount_prefix(self) -> str:
        return "/mcp"

    def register(self, registry: RouteRegistry) -> None:
        registry.register(
            method="GET",
            path="/v1/surfaces/mcp",
            handler=self._info,
            surface=self.name,
        )
        registry.register(
            method="POST",
            path="/mcp",
            handler=self._http_dispatch,
            surface=self.name,
        )
        registry.register(
            method="GET",
            path="/mcp",
            handler=self._http_dispatch,
            surface=self.name,
        )
        registry.register(
            method="DELETE",
            path="/mcp",
            handler=self._http_dispatch,
            surface=self.name,
        )
        registry.register(
            method="OPTIONS",
            path="/mcp",
            handler=self._http_dispatch,
            surface=self.name,
        )
        registry.register(
            method="GET",
            path="/mcp/sse",
            handler=self._http_dispatch,
            surface=self.name,
        )
        registry.register(
            method="POST",
            path="/mcp/messages",
            handler=self._http_dispatch,
            surface=self.name,
        )

    def _info(self, request: ServerRequest) -> ServerResponse:
        from palm.runtimes.mcp.http_bridge import mcp_http_available

        http_active = mcp_http_available()
        transports: list[str] = ["stdio"]
        if http_active:
            transports.extend(["streamable-http", "sse"])

        body: dict[str, object] = {
            "surface": self.name,
            "status": "active" if http_active else "stdio",
            "transport": transports[0] if len(transports) == 1 else transports,
            "transports": transports,
            "command": "palm-mcp",
            "endpoint": "/mcp" if http_active else None,
            "message": (
                "Palm operator MCP is available via stdio (``palm-mcp``) and, when the "
                "``mcp`` extra is installed, HTTP on ``/mcp`` (streamable) and ``/mcp/sse``."
            ),
            "detail": (
                "Stdio proxies to the REST API (PALM_BASE_URL). Native HTTP reuses the "
                "same tool surface in-process via loopback REST. Wizard input tools accept "
                "plain ``input`` strings (yes/no, choice slugs, text)—not JSON wrappers."
            ),
            "mount_prefix": self.mount_prefix,
            "env": {
                "PALM_BASE_URL": "Palm REST base URL (stdio adapter)",
                "PALM_SUBJECT": "X-Palm-Subject header for auth-enforced servers",
                "PALM_LLMS_TXT": "Optional path to docs/llms.txt for agent guide resource",
            },
        }
        if http_active:
            body["http"] = {
                "streamable_http": {
                    "path": "/mcp",
                    "accept": "application/json, text/event-stream",
                },
                "sse": {
                    "sse_path": "/mcp/sse",
                    "message_path": "/mcp/messages",
                },
            }
        return ServerResponse(status=200, body=body)

    def _http_dispatch(self, request: ServerRequest) -> ServerResponse:
        from palm.runtimes.mcp.http_bridge import (
            get_mcp_http_bridge,
            mcp_http_available,
            subject_from_request,
        )

        if not mcp_http_available():
            return ServerResponse(
                status=501,
                body={
                    "error": "mcp_extra_required",
                    "message": (
                        'Native HTTP MCP requires the optional "mcp" extra. '
                        'Install with: pip install "palmengine[mcp]"'
                    ),
                    "command": "palm-mcp",
                },
            )

        runtime = self._ctx.runtime
        base_url = getattr(runtime, "base_url", None)
        if not isinstance(base_url, str) or not base_url:
            return ServerResponse(
                status=503,
                body={
                    "error": "mcp_unavailable",
                    "message": "Server runtime base_url is not available for MCP loopback",
                },
            )

        bridge = get_mcp_http_bridge(
            base_url,
            subject=subject_from_request(request),
            ctx=self._ctx,
        )
        if bridge is None:
            return ServerResponse(
                status=503,
                body={"error": "mcp_unavailable", "message": "Failed to start MCP HTTP bridge"},
            )
        return bridge.dispatch(request)
