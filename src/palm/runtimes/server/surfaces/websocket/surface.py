"""
WebSocket surface — real-time Assist channel (0.32.1+) + Portal dogfood (0.32.4).

HTTP discovery: ``GET /v1/surfaces/websocket``
Assist channel: ``GET /ws/v1/assist`` with WebSocket upgrade (stdlib transport).
Portal UI: ``GET /portal/`` (static dogfood chat).
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from palm.common.runtimes.server.protocol import ServerRequest, ServerResponse
from palm.common.runtimes.server.surface import BaseSurface
from palm.runtimes.server.surfaces.websocket.session import (
    ASSIST_WS_PATH,
    PROTOCOL_VERSION,
)
from palm.runtimes.server.surfaces.websocket.static import portal_file_response

if TYPE_CHECKING:
    from palm.common.runtimes.server.context import ServerContext
    from palm.common.runtimes.server.registry import RouteRegistry


class WebSocketSurface(BaseSurface):
    """WebSocket Assist surface — info, upgrade path, Portal static assets."""

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
        registry.register(
            method="GET",
            path=ASSIST_WS_PATH,
            handler=self._assist_http_hint,
            surface=self.name,
        )
        registry.register(
            method="GET",
            path="/portal",
            handler=self._portal_index,
            surface=self.name,
        )
        registry.register(
            method="GET",
            path="/portal/",
            handler=self._portal_index,
            surface=self.name,
        )
        registry.register(
            method="GET",
            path="/portal/{asset}",
            handler=self._portal_asset,
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
                    "WebSocket Assist + Portal dogfood. "
                    f"WS: {ASSIST_WS_PATH} · UI: /portal/"
                ),
                "detail": "0.32.4 Portal dogfood — input schema on WS turns.",
                "mount_prefix": self.mount_prefix,
                "assist_path": ASSIST_WS_PATH,
                "portal_path": "/portal/",
                "ops": ["hello", "ping", "dispatch", "bind"],
            },
        )

    def _assist_http_hint(self, request: ServerRequest) -> ServerResponse:
        """Fallback when a non-stdlib transport hits the WS path without upgrade.

        Stdlib transport answers 101/426 itself (``diag=ws-upgrade-v4``). If you
        still see this body (``diag=surface-fallback``), the request never entered
        ``_try_websocket_upgrade`` (wrong transport, or path mismatch).
        """
        from palm import __version__ as palm_version

        lower = {str(k).lower(): str(v) for k, v in (request.headers or {}).items()}
        present = {
            "path": getattr(request, "path", None),
            "upgrade": lower.get("upgrade"),
            "connection": lower.get("connection"),
            "sec-websocket-key": bool(lower.get("sec-websocket-key")),
            "sec-websocket-version": lower.get("sec-websocket-version"),
            "cf-ray": lower.get("cf-ray"),
            "cdn-loop": lower.get("cdn-loop"),
            "header_names": sorted(lower.keys()),
        }
        missing = [
            name
            for name, ok in (
                ("Upgrade: websocket", "websocket" in (present["upgrade"] or "").lower()),
                (
                    "Connection: …Upgrade…",
                    "upgrade" in (present["connection"] or "").lower(),
                ),
                ("Sec-WebSocket-Key", present["sec-websocket-key"]),
            )
            if not ok
        ]
        return ServerResponse(
            status=426,
            body={
                "error": "upgrade_required",
                "message": (
                    f"Use WebSocket upgrade on {ASSIST_WS_PATH} "
                    "(Sec-WebSocket-Version: 13). "
                    "If this appears behind a tunnel/proxy, Upgrade headers "
                    "were not forwarded to Palm — or Palm is not on the "
                    "stdlib transport upgrade path."
                ),
                "assist_path": ASSIST_WS_PATH,
                "protocol": PROTOCOL_VERSION,
                "portal_path": "/portal/",
                "diag": "surface-fallback",
                "palm_version": palm_version,
                "handshake": present,
                "missing": missing,
            },
            headers={
                "Upgrade": "websocket",
                "X-Palm-WS-Diag": "surface-fallback",
                "X-Palm-Version": palm_version,
            },
        )

    def _portal_index(self, request: ServerRequest) -> ServerResponse:
        del request
        resp = portal_file_response("index.html")
        if resp is None:
            return ServerResponse(
                status=404,
                body={"error": "portal_missing", "message": "Portal static assets not found"},
            )
        return resp

    def _portal_asset(self, request: ServerRequest, asset: str = "") -> ServerResponse:
        del request
        resp = portal_file_response(asset or "index.html")
        if resp is None:
            return ServerResponse(
                status=404,
                body={"error": "not_found", "message": f"Unknown portal asset: {asset}"},
            )
        return resp


__all__ = ["WebSocketSurface"]
