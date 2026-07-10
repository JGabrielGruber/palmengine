"""Analytics REST routes under ``/v1/api/analytics``."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from palm.runtimes.server.surfaces.rest.analytics import handlers
from palm.runtimes.server.surfaces.rest.bindings import bind_handler
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
    auth_required: bool = True


ROUTES: tuple[RouteEntry, ...] = (
    RouteEntry(
        "list_datasets",
        "GET",
        f"{API_PREFIX}/analytics/datasets",
        "list_datasets",
        auth_required=True,
    ),
    RouteEntry(
        "describe_dataset",
        "GET",
        f"{API_PREFIX}/analytics/datasets/{{dataset}}",
        "describe_dataset",
        auth_required=True,
    ),
    RouteEntry(
        "query",
        "POST",
        f"{API_PREFIX}/analytics/query",
        "query",
        auth_required=True,
    ),
)

_HANDLERS = {
    "list_datasets": handlers.list_datasets,
    "describe_dataset": handlers.describe_dataset,
    "query": handlers.query,
}


def register_analytics_routes(
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


__all__ = ["ROUTES", "RouteEntry", "register_analytics_routes"]
