"""Explorer route registration."""

from __future__ import annotations

from typing import TYPE_CHECKING

from palm.common.runtimes.server.ssr.render import redirect
from palm.runtimes.server.surfaces.ssr.example_pages import ExamplePages
from palm.runtimes.server.surfaces.ssr.explorer import ExplorerPages
from palm.runtimes.server.surfaces.ssr.explorer.actions import ExplorerActions

if TYPE_CHECKING:
    from palm.common.runtimes.server.context import ServerContext
    from palm.common.runtimes.server.registry import RouteRegistry

_SURFACE = "explorer"

_WIKI_REDIRECTS = (
    "/wiki",
    "/wiki/flows",
    "/wiki/processes",
    "/wiki/patterns",
    "/wiki/schemas",
    "/wiki/jobs",
    "/wiki/examples",
)


def register_explorer_routes(registry: RouteRegistry, ctx: ServerContext) -> None:
    """Mount Palm Explorer and example SSR routes."""
    pages = ExplorerPages(ctx)
    actions = ExplorerActions(ctx)
    examples = ExamplePages(ctx)

    registry.register(method="GET", path="/explorer", handler=pages.overview, surface=_SURFACE)
    registry.register(
        method="GET", path="/explorer/assist", handler=pages.assist_catalog, surface=_SURFACE
    )
    registry.register(
        method="GET",
        path="/explorer/assist/scenarios/{scenario_id}",
        handler=pages.assist_scenario_detail,
        surface=_SURFACE,
    )
    registry.register(
        method="POST",
        path="/explorer/assist/scenarios/{scenario_id}/start",
        handler=actions.start_assist_scenario,
        surface=_SURFACE,
    )
    registry.register(
        method="GET",
        path="/explorer/assist/session/{session_id}",
        handler=pages.assist_session,
        surface=_SURFACE,
    )
    registry.register(method="GET", path="/explorer/flows", handler=pages.flows, surface=_SURFACE)
    registry.register(
        method="GET", path="/explorer/flows/submit", handler=pages.flow_submit, surface=_SURFACE
    )
    registry.register(
        method="POST", path="/explorer/flows/submit", handler=actions.submit_flow, surface=_SURFACE
    )
    registry.register(
        method="GET",
        path="/explorer/flows/{flow_id}",
        handler=pages.flow_detail,
        surface=_SURFACE,
    )
    registry.register(
        method="GET", path="/explorer/processes", handler=pages.processes, surface=_SURFACE
    )
    registry.register(
        method="GET",
        path="/explorer/processes/{process_id}",
        handler=pages.process_detail,
        surface=_SURFACE,
    )
    registry.register(
        method="GET", path="/explorer/resources", handler=pages.resources, surface=_SURFACE
    )
    registry.register(
        method="GET",
        path="/explorer/resources/{resource_id}",
        handler=pages.resource_detail,
        surface=_SURFACE,
    )
    registry.register(
        method="GET",
        path="/explorer/resources/{resource_id}/invoke",
        handler=pages.resource_invoke,
        surface=_SURFACE,
    )
    registry.register(
        method="POST",
        path="/explorer/resources/{resource_id}/invoke",
        handler=pages.resource_invoke_post,
        surface=_SURFACE,
    )
    registry.register(
        method="GET", path="/explorer/patterns", handler=pages.patterns, surface=_SURFACE
    )
    registry.register(
        method="GET", path="/explorer/schemas", handler=pages.schemas, surface=_SURFACE
    )
    registry.register(method="GET", path="/explorer/jobs", handler=pages.jobs, surface=_SURFACE)
    registry.register(
        method="GET", path="/explorer/jobs/{job_id}", handler=pages.job_detail, surface=_SURFACE
    )
    registry.register(
        method="POST",
        path="/explorer/jobs/{job_id}/input",
        handler=actions.provide_job_input,
        surface=_SURFACE,
    )
    registry.register(
        method="GET", path="/explorer/instances", handler=pages.instances, surface=_SURFACE
    )
    registry.register(
        method="GET",
        path="/explorer/instances/{instance_id}",
        handler=pages.instance_detail,
        surface=_SURFACE,
    )
    registry.register(
        method="POST",
        path="/explorer/instances/{instance_id}/input",
        handler=actions.provide_wizard_input,
        surface=_SURFACE,
    )
    registry.register(
        method="POST",
        path="/explorer/instances/{instance_id}/backtrack",
        handler=actions.backtrack_wizard,
        surface=_SURFACE,
    )
    registry.register(
        method="POST",
        path="/explorer/instances/{instance_id}/resume-child-wait",
        handler=actions.resume_child_wait,
        surface=_SURFACE,
    )
    registry.register(
        method="POST",
        path="/explorer/instances/{instance_id}/resume-wizard-tick",
        handler=actions.resume_wizard_tick,
        surface=_SURFACE,
    )
    registry.register(
        method="GET",
        path="/explorer/instances/{instance_id}/snapshots",
        handler=pages.snapshots,
        surface=_SURFACE,
    )
    registry.register(
        method="GET",
        path="/explorer/instances/{instance_id}/snapshots/{snapshot_id}",
        handler=pages.snapshot_detail,
        surface=_SURFACE,
    )

    registry.register(
        method="GET", path="/explorer/examples", handler=examples.index, surface=_SURFACE
    )
    registry.register(
        method="GET",
        path="/explorer/examples/wizard-preview",
        handler=examples.wizard_preview,
        surface=_SURFACE,
    )
    registry.register(
        method="GET",
        path="/explorer/examples/dashboard",
        handler=examples.dashboard,
        surface=_SURFACE,
    )

    for wiki_path in _WIKI_REDIRECTS:
        explorer_path = wiki_path.replace("/wiki", "/explorer", 1)
        registry.register(
            method="GET",
            path=wiki_path,
            handler=_redirect_to(explorer_path),
            surface=_SURFACE,
        )

    registry.register(
        method="GET",
        path="/",
        handler=lambda req: redirect("/explorer"),
        surface=_SURFACE,
    )

    registry.register(
        method="GET",
        path="/docs",
        handler=lambda req: redirect("/explorer"),
        surface=_SURFACE,
    )

    registry.register(
        method="GET", path="/v1/surfaces/explorer", handler=_surface_info, surface=_SURFACE
    )
    registry.register(
        method="GET", path="/v1/surfaces/ssr", handler=_surface_info, surface=_SURFACE
    )


def register_ssr_routes(registry: RouteRegistry, ctx: ServerContext) -> None:
    """Backward-compatible alias for :func:`register_explorer_routes`."""
    register_explorer_routes(registry, ctx)


def _redirect_to(location: str):
    def _handler(request: object) -> object:
        return redirect(location)

    return _handler


def _surface_info(request: object) -> object:
    from palm.common.runtimes.server.protocol import ServerResponse

    return ServerResponse(
        status=200,
        body={
            "surface": "explorer",
            "status": "active",
            "message": "Palm Explorer — living introspection and control hub.",
            "home": "/explorer",
            "explorer": "/explorer",
            "wiki": "/explorer",
            "docs_alias": "/docs",
            "api_docs": "/v1/docs",
            "examples": "/explorer/examples",
        },
    )
