"""REST: public event catalog + journal poll (0.42) — composition catch-up without WS."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from palm.common.events.catalog import PUBLIC_EVENT_TYPES, catalog_dict, is_public_event_type
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
    auth_required: bool = False


ROUTES: tuple[RouteEntry, ...] = (
    RouteEntry(
        "events_catalog",
        "GET",
        f"{API_PREFIX}/events/catalog",
        "events_catalog",
    ),
    RouteEntry(
        "events_journal",
        "GET",
        f"{API_PREFIX}/events/journal",
        "events_journal",
        auth_required=True,
    ),
)


def events_catalog(ctx: ServerContext, request: ServerRequest) -> ServerResponse:
    del ctx, request
    return ok(catalog_dict())


def events_journal(ctx: ServerContext, request: ServerRequest) -> ServerResponse:
    auth_error = require_auth(ctx, request)
    if auth_error is not None:
        return auth_error

    host = getattr(ctx, "host", None) or getattr(ctx, "_host", None)
    journal = None
    if host is not None:
        journal = getattr(host, "event_journal", None)
    if journal is None:
        return ServerResponse(
            status=503,
            body={"error": "event_journal_unavailable", "message": "event journal not available"},
        )

    try:
        after = int(request.query.get("after") or request.query.get("since_offset") or 0)
    except (TypeError, ValueError):
        after = 0
    try:
        limit = min(500, max(1, int(request.query.get("limit") or 100)))
    except (TypeError, ValueError):
        limit = 100

    types_raw = str(request.query.get("types") or "").strip()
    type_filter = None
    if types_raw:
        type_filter = frozenset(
            t for t in (x.strip() for x in types_raw.split(",")) if is_public_event_type(t)
        )

    entries = journal.read_after(
        after,
        limit=limit,
        event_types=type_filter if type_filter else PUBLIC_EVENT_TYPES,
    )
    rows: list[dict[str, Any]] = []
    for e in entries:
        rows.append(
            {
                "offset": e.offset,
                "type": e.event_type,
                "payload": dict(e.payload or {}),
                "ts": e.timestamp,
                "id": e.id,
            }
        )
    last = rows[-1]["offset"] if rows else after
    return ok(
        {
            "after": after,
            "limit": limit,
            "count": len(rows),
            "latest_offset": journal.latest_offset(),
            "last_offset": last,
            "events": rows,
            "ws": "/ws/v1/events",
        }
    )


_HANDLERS = {
    "events_catalog": events_catalog,
    "events_journal": events_journal,
}


def register_events_routes(registry: RouteRegistry, ctx: ServerContext, *, surface: str) -> None:
    for entry in ROUTES:
        registry.register(
            method=entry.method,
            path=entry.path,
            handler=bind_handler(ctx, _HANDLERS[entry.handler_name]),
            surface=surface,
            auth_required=entry.auth_required,
        )


__all__ = ["ROUTES", "register_events_routes"]
