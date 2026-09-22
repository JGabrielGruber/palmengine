"""WebSocket surface — Assist real-time channel (0.32+)."""

from bundles.standard.runtimes.server.surfaces.websocket.session import (
    ASSIST_WS_PATH,
    PROTOCOL_VERSION,
)
from bundles.standard.runtimes.server.surfaces.websocket.surface import WebSocketSurface

__all__ = ["ASSIST_WS_PATH", "PROTOCOL_VERSION", "WebSocketSurface"]
