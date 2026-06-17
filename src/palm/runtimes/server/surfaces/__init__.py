"""Concrete server surfaces — REST, WebSocket, MCP, SSR."""

from __future__ import annotations

from typing import TYPE_CHECKING

from palm.runtimes.server.surfaces.mcp.surface import McpSurface
from palm.runtimes.server.surfaces.rest import RestSurface
from palm.runtimes.server.surfaces.ssr.surface import SsrSurface
from palm.runtimes.server.surfaces.websocket.surface import WebSocketSurface

if TYPE_CHECKING:
    from palm.common.runtimes.server.context import ServerContext


def default_surfaces(ctx: ServerContext) -> list[object]:
    """Built-in surfaces shipped with the Palm server runtime."""
    planned = [
        WebSocketSurface(ctx),
        McpSurface(ctx),
        SsrSurface(ctx),
    ]
    names = ["rest", *(surface.name for surface in planned)]
    return [RestSurface(ctx, surface_names=names), *planned]


__all__ = [
    "McpSurface",
    "RestSurface",
    "SsrSurface",
    "WebSocketSurface",
    "default_surfaces",
]