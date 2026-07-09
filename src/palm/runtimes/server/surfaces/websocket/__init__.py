"""WebSocket surface — Assist real-time channel (0.32+)."""

from palm.runtimes.server.surfaces.websocket.session import (
    ASSIST_WS_PATH,
    PROTOCOL_VERSION,
)
from palm.runtimes.server.surfaces.websocket.surface import WebSocketSurface

__all__ = ["ASSIST_WS_PATH", "PROTOCOL_VERSION", "WebSocketSurface"]
