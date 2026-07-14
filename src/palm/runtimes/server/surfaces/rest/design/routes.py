"""Design service REST routes under ``/v1/api/design``."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from palm.runtimes.server.surfaces.rest.bindings import bind_handler
from palm.runtimes.server.surfaces.rest.design import handlers
from palm.runtimes.server.surfaces.rest.prefix import API_PREFIX

if TYPE_CHECKING:
    from palm.common.runtimes.server.context import ServerContext
    from palm.common.runtimes.server.registry import RouteRegistry


@dataclass(frozen=True)
class RouteEntry:
    route_id: str
    method: str
    path: str
    handler_name: str
    auth_required: bool = False


ROUTES: tuple[RouteEntry, ...] = (
    RouteEntry("list_proposals", "GET", f"{API_PREFIX}/design/proposals", "list_proposals"),
    RouteEntry(
        "propose_flow",
        "POST",
        f"{API_PREFIX}/design/proposals",
        "propose_flow",
        auth_required=True,
    ),
    RouteEntry(
        "propose_dashboard",
        "POST",
        f"{API_PREFIX}/design/dashboards",
        "propose_dashboard",
        auth_required=True,
    ),
    RouteEntry(
        "publish_dashboard",
        "POST",
        f"{API_PREFIX}/design/dashboards/publish",
        "publish_dashboard",
        auth_required=True,
    ),
    RouteEntry(
        "get_proposal",
        "GET",
        f"{API_PREFIX}/design/proposals/{{proposal_id}}",
        "get_proposal",
    ),
    RouteEntry(
        "discard_proposal",
        "DELETE",
        f"{API_PREFIX}/design/proposals/{{proposal_id}}",
        "discard_proposal",
        auth_required=True,
    ),
    RouteEntry(
        "validate_proposal",
        "POST",
        f"{API_PREFIX}/design/proposals/{{proposal_id}}/validate",
        "validate_proposal",
        auth_required=True,
    ),
    RouteEntry(
        "analyze_proposal_impact",
        "GET",
        f"{API_PREFIX}/design/proposals/{{proposal_id}}/impact",
        "analyze_proposal_impact",
    ),
    RouteEntry(
        "commit_proposal",
        "POST",
        f"{API_PREFIX}/design/proposals/{{proposal_id}}/commit",
        "commit_proposal",
        auth_required=True,
    ),
)

_HANDLERS = {
    "list_proposals": handlers.list_proposals,
    "propose_flow": handlers.propose_flow,
    "propose_dashboard": handlers.propose_dashboard,
    "publish_dashboard": handlers.publish_dashboard,
    "get_proposal": handlers.get_proposal,
    "discard_proposal": handlers.discard_proposal,
    "validate_proposal": handlers.validate_proposal,
    "analyze_proposal_impact": handlers.analyze_proposal_impact,
    "commit_proposal": handlers.commit_proposal,
}


def register_design_routes(
    registry: RouteRegistry,
    ctx: ServerContext,
    *,
    surface: str,
) -> None:
    for entry in ROUTES:
        fn = _HANDLERS[entry.handler_name]
        registry.register(
            method=entry.method,
            path=entry.path,
            handler=bind_handler(ctx, fn),
            surface=surface,
            auth_required=entry.auth_required,
        )


__all__ = ["ROUTES", "RouteEntry", "register_design_routes"]