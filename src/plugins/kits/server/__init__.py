"""Server kit — contracts for HTTP protocol, routes, transport, and webhook health.

**Kit home:** :mod:`plugins.kits.server`.

The kit names what a composition root must provide: a normalized request and
response, a mountable surface, a :class:`~plugins.kits.server.transport.TransportApp`
a wire may dispatch, and a webhook health snapshot. The root owns wiring.
The bundled server runtime is one such root. ``ServerWebhookBridge`` is
exported lazily.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from plugins.kits.registry import register_kit
from plugins.kits.server.middleware import (
    PALM_SESSION_COOKIE,
    PALM_SESSION_HEADER,
    PALM_SUBJECT_HEADER,
    authenticate_request,
    current_principal_id,
    extract_system_session_hint,
    parse_cookie_header,
    require_session_service,
    resolve_session_plane,
    resolve_session_service,
    set_cookie_header_value,
)
from plugins.kits.server.protocol import (
    HttpMethod,
    ServerRequest,
    ServerResponse,
    ServerSurface,
)
from plugins.kits.server.registry import RouteRegistry, RouteSpec, SurfaceRegistry
from plugins.kits.server.responses import error_response
from plugins.kits.server.surface import BaseSurface
from plugins.kits.server.transport import (
    BaseTransport,
    TransportApp,
    TransportRegistry,
    transport_registry,
)

register_kit(
    "server",
    description="HTTP protocol, routes, transport, CQRS bridge, SSR helpers",
    module="palm.kits.server",
)

if TYPE_CHECKING:
    from plugins.kits.server.webhooks import ServerWebhookBridge

_LAZY_EXPORTS = {
    "ServerWebhookBridge": "palm.kits.server.webhooks",
}


def __getattr__(name: str) -> object:
    target = _LAZY_EXPORTS.get(name)
    if target is not None:
        import importlib

        return getattr(importlib.import_module(target), name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = [
    "BaseSurface",
    "BaseTransport",
    "TransportApp",
    "HttpMethod",
    "PALM_SESSION_COOKIE",
    "PALM_SESSION_HEADER",
    "PALM_SUBJECT_HEADER",
    "RouteRegistry",
    "RouteSpec",
    "ServerRequest",
    "ServerResponse",
    "ServerSurface",
    "ServerWebhookBridge",
    "SurfaceRegistry",
    "TransportRegistry",
    "authenticate_request",
    "current_principal_id",
    "error_response",
    "extract_system_session_hint",
    "parse_cookie_header",
    "require_session_service",
    "resolve_session_plane",
    "resolve_session_service",
    "set_cookie_header_value",
    "transport_registry",
]
