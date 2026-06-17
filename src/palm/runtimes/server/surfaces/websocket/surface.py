"""
WebSocket surface — extension point for real-time interaction (0.11+).
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from palm.common.runtimes.server.protocol import ServerRequest, ServerResponse
from palm.common.runtimes.server.surface import BaseSurface

if TYPE_CHECKING:
    from palm.common.runtimes.server.context import ServerContext
    from palm.common.runtimes.server.registry import RouteRegistry


class WebSocketSurface(BaseSurface):
    """Placeholder surface documenting the WebSocket extension point."""

    def __init__(self, ctx: ServerContext) -> None:
        self._ctx = ctx

    @property
    def name(self) -> str:
        return "websocket"

    @property
    def mount_prefix(self) -> str:
        return "/ws"

    def register(self, registry: RouteRegistry) -> None:
        registry.register(
            method="GET",
            path="/v1/surfaces/websocket",
            handler=self._info,
            surface=self.name,
        )

    def _info(self, request: ServerRequest) -> ServerResponse:
        return ServerResponse(
            status=501,
            body={
                "surface": self.name,
                "status": "planned",
                "message": "WebSocket transport will bind to this surface in a future release.",
                "detail": "WebSocket transport will bind to this surface in a future release.",
                "mount_prefix": self.mount_prefix,
            },
        )