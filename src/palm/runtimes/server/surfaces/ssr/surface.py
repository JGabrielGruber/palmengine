"""
SSR surface — server-rendered wiki, documentation hub, and operator views.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from palm.common.runtimes.server.surface import BaseSurface
from palm.runtimes.server.surfaces.ssr.routes import register_ssr_routes

if TYPE_CHECKING:
    from palm.common.runtimes.server.context import ServerContext
    from palm.common.runtimes.server.registry import RouteRegistry


class SsrSurface(BaseSurface):
    """Human-facing HTML surface — dynamic wiki introspecting the running engine."""

    def __init__(self, ctx: ServerContext) -> None:
        self._ctx = ctx

    @property
    def name(self) -> str:
        return "ssr"

    @property
    def mount_prefix(self) -> str:
        return "/wiki"

    def register(self, registry: RouteRegistry) -> None:
        register_ssr_routes(registry, self._ctx)