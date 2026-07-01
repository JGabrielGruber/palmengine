"""
REST route metadata — declarative table without handler imports.

Shared by route registration, OpenAPI generation, and HTML docs.

Legacy job/instance/plan monolith routes were removed in 0.17 — use
``/v1/api/system``, ``/v1/api/flows``, ``/v1/api/processes``, and
``/v1/api/definitions`` instead.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

RouteId = Literal[
    "health",
    "openapi",
    "docs",
]


@dataclass(frozen=True)
class RouteDefinition:
    """Declarative route with OpenAPI-oriented metadata."""

    route_id: RouteId
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
    return (
        RouteDefinition(
            route_id="health",
            method="GET",
            path="/health",
            group="Meta",
            summary="Health check",
            description="Runtime status, mounted surfaces, and documentation links.",
        ),
        RouteDefinition(
            route_id="openapi",
            method="GET",
            path="/v1/openapi.json",
            group="Meta",
            summary="OpenAPI document",
            description="Machine-readable API specification (OpenAPI 3.0).",
        ),
        RouteDefinition(
            route_id="docs",
            method="GET",
            path="/v1/docs",
            group="Meta",
            summary="API documentation",
            description="Human-readable HTML overview with endpoint groups.",
        ),
    )