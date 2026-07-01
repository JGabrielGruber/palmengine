"""
REST route metadata — declarative table without handler imports.

Shared by route registration, OpenAPI generation, and HTML docs.

Legacy job/instance/plan monolith routes were removed in 0.17 — use
``/v1/api/system``, ``/v1/api/flows``, ``/v1/api/processes``, and
``/v1/api/definitions`` instead.
"""

from __future__ import annotations

from dataclasses import dataclass

RouteId = str


@dataclass(frozen=True)
class RouteDefinition:
    """Declarative route with OpenAPI-oriented metadata."""

    route_id: str
    method: str
    path: str
    group: str
    summary: str
    description: str = ""
    auth_required: bool = False
    request_schema: str | None = None
    query_schema: str | None = None
    response_status: int = 200


def rest_routes() -> tuple[RouteDefinition, ...]:
    """Return the full REST route table grouped by resource."""
    from palm.runtimes.server.surfaces.rest.openapi_registry import rest_routes as _all_routes

    return _all_routes()