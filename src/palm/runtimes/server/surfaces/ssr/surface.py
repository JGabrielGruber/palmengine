"""
Explorer surface — server-rendered introspection hub and operator views.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from palm.common.runtimes.server.surface import BaseSurface
from palm.runtimes.server.surfaces.ssr.routes import register_explorer_routes

if TYPE_CHECKING:
    from palm.common.runtimes.server.registry import RouteRegistry
    from palm.runtimes.server.context import ServerContext


class ExplorerSurface(BaseSurface):
    """Human-facing HTML surface — Palm Explorer introspecting the running engine."""

    def __init__(self, ctx: ServerContext) -> None:
        self._ctx = ctx

    @property
    def name(self) -> str:
        return "explorer"

    @property
    def mount_prefix(self) -> str:
        return "/explorer"

    def register(self, registry: RouteRegistry) -> None:
        register_explorer_routes(registry, self._ctx)


SsrSurface = ExplorerSurface
