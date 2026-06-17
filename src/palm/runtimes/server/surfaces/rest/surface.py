"""
REST surface — HTTP JSON API for plans, jobs, and instances.

Routes are declared in :mod:`routes` and handlers are split by resource under
:mod:`handlers`.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from palm.common.runtimes.server.surface import BaseSurface
from palm.runtimes.server.surfaces.rest.routes import register_routes

if TYPE_CHECKING:
    from palm.common.runtimes.server.context import ServerContext
    from palm.common.runtimes.server.registry import RouteRegistry


class RestSurface(BaseSurface):
    """
    Default REST interaction model.

    Mounts grouped routes under ``/v1`` plus ``/health``. OpenAPI and HTML docs
    are served from :func:`~palm.runtimes.server.surfaces.rest.routes.rest_routes`.
    """

    def __init__(self, ctx: ServerContext, *, surface_names: list[str] | None = None) -> None:
        self._ctx = ctx
        self._surface_names = surface_names or []

    @property
    def name(self) -> str:
        return "rest"

    def register(self, registry: RouteRegistry) -> None:
        register_routes(
            registry,
            self._ctx,
            surface=self.name,
            surface_names=self._surface_names,
        )