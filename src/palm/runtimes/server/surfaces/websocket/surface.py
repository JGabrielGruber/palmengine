"""
WebSocket surface — real-time Assist channel (0.32.1+).

HTTP discovery: ``GET /v1/surfaces/websocket``
Assist channel: ``GET /ws/v1/assist`` with WebSocket upgrade (handled by stdlib transport).
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from palm.common.runtimes.server.protocol import ServerRequest, ServerResponse
from palm.common.runtimes.server.surface import BaseSurface
from palm.runtimes.server.surfaces.websocket.session import (
    ASSIST_WS_PATH,
    PROTOCOL_VERSION,
)

if TYPE_CHECKING:
    from palm.common.runtimes.server.context import ServerContext
    from palm.common.runtimes.server.registry import RouteRegistry


class WebSocketSurface(BaseSurface):
    """WebSocket Assist surface — info route + upgrade path metadata."""

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
        # HTTP GET without upgrade returns usage (upgrade is intercepted in transport)
        registry.register(
            method="GET",
            path=ASSIST_WS_PATH,
            handler=self._assist_http_hint,
            surface=self.name,
        )

    def _info(self, request: ServerRequest) -> ServerResponse:
        del request
        return ServerResponse(
            status=200,
            body={
                "surface": self.name,
                "status": "live",
                "protocol": PROTOCOL_VERSION,
                "message": (
                    "WebSocket Assist channel is available. "
                    f"Connect with Upgrade: websocket to {ASSIST_WS_PATH}."
                ),
                "detail": "0.32.2 assist channel — hello/ping/dispatch→turn.",
                "mount_prefix": self.mount_prefix,
                "assist_path": ASSIST_WS_PATH,
                "ops": ["hello", "ping", "dispatch"],
            },
        )

    def _assist_http_hint(self, request: ServerRequest) -> ServerResponse:
        del request
        return ServerResponse(
            status=426,
            body={
                "error": "upgrade_required",
                "message": (
                    f"Use WebSocket upgrade on {ASSIST_WS_PATH} "
                    "(Sec-WebSocket-Version: 13)."
                ),
                "assist_path": ASSIST_WS_PATH,
                "protocol": PROTOCOL_VERSION,
            },
            headers={"Upgrade": "websocket"},
        )


__all__ = ["WebSocketSurface"]
