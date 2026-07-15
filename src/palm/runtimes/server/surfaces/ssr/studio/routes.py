"""Studio route registration."""

from __future__ import annotations

from typing import TYPE_CHECKING

from palm.runtimes.server.surfaces.ssr.studio.api.handlers import StudioApiHandlers
from palm.runtimes.server.surfaces.ssr.studio.pages import StudioPages

if TYPE_CHECKING:
    from palm.common.runtimes.server.registry import RouteRegistry
    from palm.runtimes.server.context import ServerContext

_SURFACE = "studio"


def register_studio_routes(registry: RouteRegistry, ctx: ServerContext) -> None:
    """Mount Palm Studio SPA routes and surface discovery."""
    pages = StudioPages(ctx)
    api = StudioApiHandlers(ctx)

    registry.register(method="GET", path="/studio", handler=pages.index, surface=_SURFACE)
    registry.register(
        method="GET", path="/v1/studio/palette", handler=api.palette, surface=_SURFACE
    )
    registry.register(
        method="GET", path="/v1/studio/drafts", handler=api.list_drafts, surface=_SURFACE
    )
    registry.register(
        method="GET", path="/v1/studio/drafts/{draft_id}", handler=api.get_draft, surface=_SURFACE
    )
    registry.register(
        method="POST", path="/v1/studio/drafts", handler=api.save_draft, surface=_SURFACE
    )
    registry.register(
        method="GET",
        path="/v1/studio/extensions",
        handler=api.extensions,
        surface=_SURFACE,
    )
    registry.register(
        method="POST",
        path="/v1/studio/definitions/flows",
        handler=api.save_flow,
        surface=_SURFACE,
    )
    registry.register(
        method="POST",
        path="/v1/studio/definitions/processes",
        handler=api.save_process,
        surface=_SURFACE,
    )
    registry.register(
        method="GET",
        path="/v1/studio/templates",
        handler=api.list_templates,
        surface=_SURFACE,
    )
    registry.register(
        method="GET",
        path="/v1/studio/templates/{template_id}",
        handler=api.get_template,
        surface=_SURFACE,
    )
    registry.register(
        method="GET",
        path="/studio/assets/{filename}",
        handler=pages.assets_file,
        surface=_SURFACE,
    )
    registry.register(
        method="GET",
        path="/studio/icons/{filename}",
        handler=pages.icons_file,
        surface=_SURFACE,
    )
    registry.register(
        method="GET",
        path="/studio/{filename}",
        handler=pages.root_file,
        surface=_SURFACE,
    )
    registry.register(
        method="GET",
        path="/v1/surfaces/studio",
        handler=_surface_info,
        surface=_SURFACE,
    )


def _surface_info(request: object) -> object:
    from palm.common.runtimes.server.protocol import ServerResponse

    return ServerResponse(
        status=200,
        body={
            "surface": "studio",
            "status": "active",
            "message": "Palm Studio — visual builder for flows, processes, wizards, and resources.",
            "home": "/studio",
            "explorer": "/explorer",
            "api_docs": "/v1/docs",
        },
    )
