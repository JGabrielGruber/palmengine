"""Shared server infrastructure — protocol, routing, transport, and CQRS bridging.

The **composition roots** ``ServerApp`` / ``ServerContext`` relocated to
``palm.runtimes.server`` in 0.48.7 (PD-013) — a composition root that instantiates
the service layer belongs in ``runtimes``, not ``common``. What remains here is
reusable server *infrastructure*. ``ServerWebhookBridge`` stays (it only references
``ServerContext`` under ``TYPE_CHECKING``) and is exported lazily.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from palm.common.runtimes.server.middleware import (
    PALM_SUBJECT_HEADER,
    authenticate_request,
    current_principal_id,
)
from palm.common.runtimes.server.protocol import (
    HttpMethod,
    ServerRequest,
    ServerResponse,
    ServerSurface,
)
from palm.common.runtimes.server.registry import RouteRegistry, RouteSpec, SurfaceRegistry
from palm.common.runtimes.server.responses import error_response
from palm.common.runtimes.server.surface import BaseSurface
from palm.common.runtimes.server.transport import (
    BaseTransport,
    TransportRegistry,
    transport_registry,
)

if TYPE_CHECKING:
    from palm.common.runtimes.server.webhooks import ServerWebhookBridge

# ServerWebhookBridge is loaded lazily to keep this __init__ free of anything that
# could re-introduce a service-layer import at package-import time.
_LAZY_EXPORTS = {
    "ServerWebhookBridge": "palm.common.runtimes.server.webhooks",
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
    "HttpMethod",
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
    "transport_registry",
]
