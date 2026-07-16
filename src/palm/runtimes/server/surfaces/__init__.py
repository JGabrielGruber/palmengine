"""Concrete server surfaces — REST, WebSocket, MCP, SSR."""

from __future__ import annotations

from typing import TYPE_CHECKING

from palm.runtimes.server.surfaces.mcp.surface import McpSurface
from palm.runtimes.server.surfaces.rest import RestSurface
from palm.runtimes.server.surfaces.ssr.studio.surface import StudioSurface
from palm.runtimes.server.surfaces.ssr.surface import ExplorerSurface, SsrSurface
from palm.runtimes.server.surfaces.websocket.surface import WebSocketSurface

if TYPE_CHECKING:
    from palm.runtimes.server.context import ServerContext


def default_surfaces(
    ctx: ServerContext,
    *,
    only: tuple[str, ...] | frozenset[str] | None = None,
) -> list[object]:
    """Built-in surfaces shipped with the Palm server runtime.

    ``only`` (a ``CompositionProfile.surfaces``) restricts which surfaces are mounted,
    by name; ``None`` mounts them all (the default). Surface ``__init__`` is
    side-effect-free — filtering the returned list is what selects them.
    """
    planned = [
        WebSocketSurface(ctx),
        McpSurface(ctx),
        ExplorerSurface(ctx),
        StudioSurface(ctx),
    ]
    if only is not None:
        planned = [surface for surface in planned if surface.name in only]
    include_rest = only is None or "rest" in only
    names = [*(["rest"] if include_rest else []), *(surface.name for surface in planned)]
    if include_rest:
        return [RestSurface(ctx, surface_names=names), *planned]
    return list(planned)


__all__ = [
    "ExplorerSurface",
    "McpSurface",
    "RestSurface",
    "SsrSurface",
    "StudioSurface",
    "WebSocketSurface",
    "default_surfaces",
]
