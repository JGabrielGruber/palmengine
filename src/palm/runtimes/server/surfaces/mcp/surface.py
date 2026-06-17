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
    """Placeholder surface for future MCP tool/resource exposure."""

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
            status=501,
            body={
                "surface": self.name,
                "status": "planned",
                "message": "MCP integration will register tools and resources here.",
                "detail": "MCP integration will register tools and resources here.",
                "mount_prefix": self.mount_prefix,
            },
        )
