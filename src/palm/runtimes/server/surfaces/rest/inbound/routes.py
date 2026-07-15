"""REST: inbound resource webhook ingress (0.43)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from palm.common.runtimes.server.protocol import ServerRequest, ServerResponse
from palm.runtimes.server.surfaces.rest.bindings import bind_handler
from palm.runtimes.server.surfaces.rest.handlers.base import require_auth
from palm.runtimes.server.surfaces.rest.prefix import API_PREFIX
from palm.runtimes.server.surfaces.rest.responses import ok

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
        "inbound_list",
        "GET",
        f"{API_PREFIX}/inbound",
        "inbound_list",
        auth_required=True,
    ),
    RouteEntry(
        "inbound_post",
        "POST",
        f"{API_PREFIX}/inbound/{{resource_name}}",
        "inbound_post",
        auth_required=True,
    ),
)


def _host_inbound(ctx: ServerContext) -> Any:
    host = getattr(ctx, "host", None) or getattr(ctx, "_host", None)
    if host is None:
        return None
    return getattr(host, "inbound", None)


def inbound_list(ctx: ServerContext, request: ServerRequest) -> ServerResponse:
    auth_error = require_auth(ctx, request)
    if auth_error is not None:
        return auth_error
    svc = _host_inbound(ctx)
    if svc is None:
        return ServerResponse(
            status=503,
            body={
                "error": "inbound_unavailable",
                "message": "inbound bindings not available",
            },
        )
    # refresh scan so design-time new resources appear
    try:
        host = getattr(ctx, "host", None) or getattr(ctx, "_host", None)
        if host is not None and hasattr(host, "reload_inbound_bindings"):
            host.reload_inbound_bindings()
    except Exception:
        pass
    return ok({"bindings": svc.list_bindings(), "count": len(svc.list_bindings())})


def inbound_post(
    ctx: ServerContext,
    request: ServerRequest,
    resource_name: str = "",
) -> ServerResponse:
    auth_error = require_auth(ctx, request)
    if auth_error is not None:
        return auth_error
    svc = _host_inbound(ctx)
    if svc is None:
        return ServerResponse(
            status=503,
            body={
                "error": "inbound_unavailable",
                "message": "inbound bindings not available",
            },
        )
    name = str(resource_name or "").strip()
    if not name:
        return ServerResponse(
            status=400,
            body={"error": "missing_resource", "message": "resource_name required"},
        )
    body = request.body if isinstance(request.body, (dict, list)) else {}
    headers = {str(k): str(v) for k, v in (request.headers or {}).items()}
    try:
        result = svc.handle_webhook(name, body=body, headers=headers)
    except KeyError:
        return ServerResponse(
            status=404,
            body={
                "error": "inbound_not_found",
                "message": f"no inbound resource {name!r}",
            },
        )
    except PermissionError as exc:
        return ServerResponse(
            status=403,
            body={"error": "inbound_forbidden", "message": str(exc)},
        )
    except ValueError as exc:
        return ServerResponse(
            status=400,
            body={"error": "inbound_invalid", "message": str(exc)},
        )
    return ServerResponse(status=202, body=result)


_HANDLERS = {
    "inbound_list": inbound_list,
    "inbound_post": inbound_post,
}


def register_inbound_routes(registry: RouteRegistry, ctx: ServerContext, *, surface: str) -> None:
    for entry in ROUTES:
        registry.register(
            method=entry.method,
            path=entry.path,
            handler=bind_handler(ctx, _HANDLERS[entry.handler_name]),
            surface=surface,
            auth_required=entry.auth_required,
        )


__all__ = ["ROUTES", "register_inbound_routes"]
