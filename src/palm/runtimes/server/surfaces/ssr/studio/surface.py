"""
Studio surface — Svelte SPA for visual flow, process, wizard, and resource building.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from palm.common.runtimes.server.surface import BaseSurface
from palm.runtimes.server.surfaces.ssr.studio.routes import register_studio_routes

if TYPE_CHECKING:
    from palm.common.runtimes.server.registry import RouteRegistry
    from palm.runtimes.server.context import ServerContext


class StudioSurface(BaseSurface):
    """Visual builder SPA mounted at ``/studio``."""

    def __init__(self, ctx: ServerContext) -> None:
        self._ctx = ctx

    @property
    def name(self) -> str:
        return "studio"

    @property
    def mount_prefix(self) -> str:
        return "/studio"

    def register(self, registry: RouteRegistry) -> None:
        register_studio_routes(registry, self._ctx)
