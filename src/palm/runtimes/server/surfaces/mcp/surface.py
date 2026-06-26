"""
MCP surface — extension point for Model Context Protocol integration.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from palm.common.runtimes.server.protocol import ServerRequest, ServerResponse
from palm.common.runtimes.server.surface import BaseSurface

if TYPE_CHECKING:
    from palm.common.runtimes.server.context import ServerContext
    from palm.common.runtimes.server.registry import RouteRegistry


class McpSurface(BaseSurface):
    """Discovery surface for the stdio MCP adapter (``palm-mcp``)."""

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

    def _info(self, request: ServerRequest) -> ServerResponse:
        return ServerResponse(
            status=200,
            body={
                "surface": self.name,
                "status": "stdio",
                "transport": "stdio",
                "command": "palm-mcp",
                "message": (
                    "Run the Palm MCP adapter as a stdio subprocess. "
                    "It proxies to the REST API (PALM_BASE_URL, default "
                    "http://127.0.0.1:8080)."
                ),
                "detail": (
                    "Native HTTP/SSE MCP on this mount prefix is planned. "
                    "Use ``palm-mcp`` for Cursor/Grok agent integration today."
                ),
                "mount_prefix": self.mount_prefix,
                "env": {
                    "PALM_BASE_URL": "Palm REST base URL",
                    "PALM_SUBJECT": "X-Palm-Subject header for auth-enforced servers",
                    "PALM_LLMS_TXT": "Optional path to docs/llms.txt for agent guide resource",
                },
            },
        )
