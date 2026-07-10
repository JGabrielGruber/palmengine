"""Analytics REST routes under ``/v1/api/analytics`` + static ``/analytics`` dogfood."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from palm.common.runtimes.server.protocol import ServerRequest, ServerResponse
from palm.runtimes.server.surfaces.rest.analytics import handlers
from palm.runtimes.server.surfaces.rest.analytics.static import analytics_file_response
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
    RouteEntry(
        "list_dashboards",
        "GET",
        f"{API_PREFIX}/analytics/dashboards",
        "list_dashboards",
        auth_required=True,
    ),
    RouteEntry(
        "get_dashboard",
        "GET",
        f"{API_PREFIX}/analytics/dashboards/{{dashboard}}",
        "get_dashboard",
        auth_required=True,
    ),
    RouteEntry(
        "render_dashboard",
        "GET",
        f"{API_PREFIX}/analytics/dashboards/{{dashboard}}/render",
        "render_dashboard",
        auth_required=True,
    ),
    RouteEntry(
        "render_dashboard_post",
        "POST",
        f"{API_PREFIX}/analytics/dashboards/{{dashboard}}/render",
        "render_dashboard",
        auth_required=True,
    ),
)

_HANDLERS = {
    "list_datasets": handlers.list_datasets,
    "describe_dataset": handlers.describe_dataset,
    "query": handlers.query,
    "list_dashboards": handlers.list_dashboards,
    "get_dashboard": handlers.get_dashboard,
    "render_dashboard": handlers.render_dashboard,
}


def _static_index(_ctx: Any, _request: ServerRequest) -> ServerResponse:
    resp = analytics_file_response("index.html")
    if resp is None:
        return ServerResponse(status=404, body={"error": "analytics_ui_missing"})
    return resp


def _static_asset(
    _ctx: Any,
    _request: ServerRequest,
    *,
    asset: str = "",
) -> ServerResponse:
    resp = analytics_file_response(asset or "index.html")
    if resp is None:
        return ServerResponse(status=404, body={"error": "not_found", "path": asset})
    return resp


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
    # Dogfood UI (no auth — same as Portal shell; API still requires subject)
    for path, handler in (
        ("/analytics", _static_index),
        ("/analytics/", _static_index),
        ("/analytics/{asset}", _static_asset),
    ):
        registry.register(
            method="GET",
            path=path,
            handler=bind_handler(ctx, handler),
            surface=surface,
            auth_required=False,
        )


__all__ = ["ROUTES", "RouteEntry", "register_analytics_routes"]
