"""SSR route registration."""

from __future__ import annotations

from typing import TYPE_CHECKING

from palm.common.runtimes.server.ssr.render import redirect
from palm.runtimes.server.surfaces.ssr.example_pages import ExamplePages
from palm.runtimes.server.surfaces.ssr.wiki.pages import WikiPages

if TYPE_CHECKING:
    from palm.common.runtimes.server.context import ServerContext
    from palm.common.runtimes.server.registry import RouteRegistry


def register_ssr_routes(registry: RouteRegistry, ctx: ServerContext) -> None:
    """Mount wiki and example SSR routes."""
    wiki = WikiPages(ctx)
    examples = ExamplePages(ctx)
    surface = "ssr"

    registry.register(method="GET", path="/wiki", handler=wiki.overview, surface=surface)
    registry.register(method="GET", path="/wiki/flows", handler=wiki.flows, surface=surface)
    registry.register(method="GET", path="/wiki/flows/{flow_id}", handler=wiki.flow_detail, surface=surface)
    registry.register(method="GET", path="/wiki/processes", handler=wiki.processes, surface=surface)
    registry.register(
        method="GET",
        path="/wiki/processes/{process_id}",
        handler=wiki.process_detail,
        surface=surface,
    )
    registry.register(method="GET", path="/wiki/patterns", handler=wiki.patterns, surface=surface)
    registry.register(method="GET", path="/wiki/schemas", handler=wiki.schemas, surface=surface)
    registry.register(method="GET", path="/wiki/jobs", handler=wiki.jobs, surface=surface)
    registry.register(method="GET", path="/wiki/jobs/{job_id}", handler=wiki.job_detail, surface=surface)
    registry.register(
        method="GET",
        path="/wiki/instances/{instance_id}/snapshots",
        handler=wiki.snapshots,
        surface=surface,
    )
    registry.register(
        method="GET",
        path="/wiki/instances/{instance_id}/snapshots/{snapshot_id}",
        handler=wiki.snapshot_detail,
        surface=surface,
    )

    registry.register(method="GET", path="/wiki/examples", handler=examples.index, surface=surface)
    registry.register(
        method="GET",
        path="/wiki/examples/wizard-preview",
        handler=examples.wizard_preview,
        surface=surface,
    )
    registry.register(
        method="GET",
        path="/wiki/examples/dashboard",
        handler=examples.dashboard,
        surface=surface,
    )

    registry.register(
        method="GET",
        path="/docs",
        handler=lambda req: redirect("/wiki"),
        surface=surface,
    )

    registry.register(method="GET", path="/v1/surfaces/ssr", handler=_surface_info, surface=surface)


def _surface_info(request: object) -> object:
    from palm.common.runtimes.server.protocol import ServerResponse

    return ServerResponse(
        status=200,
        body={
            "surface": "ssr",
            "status": "active",
            "message": "Server-rendered wiki and documentation hub.",
            "wiki": "/wiki",
            "docs_alias": "/docs",
            "api_docs": "/v1/docs",
            "examples": "/wiki/examples",
        },
    )