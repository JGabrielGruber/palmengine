"""Shared server infrastructure — protocol, routing, transport, and CQRS bridging.

The composition-root exports (``ServerApp``, ``ServerContext``, ``ServerWebhookBridge``)
are **lazy** (PEP 562 ``__getattr__``): they pull ``ServerContext``, which imports
the service layer, so eager-importing them here creates a latent cycle —
``services.definitions.service`` → ``server.plans`` → this ``__init__`` →
``ServerContext`` → ``services.definitions``. Loading them lazily means importing
server *infra* (e.g. ``.plans``, ``.middleware``) never triggers the service layer.
Infra exports stay eager. (T2 / 0.48.6 — precursor to relocating ``ServerContext``, PD-013.)
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
    from palm.common.runtimes.server.app import ServerApp, create_server_app
    from palm.common.runtimes.server.context import ServerContext
    from palm.common.runtimes.server.webhooks import ServerWebhookBridge

# Composition-root exports pull the service layer via ServerContext — load them
# lazily so importing server infra never triggers the cycle. Mirrors common/__init__.
_LAZY_EXPORTS = {
    "ServerApp": "palm.common.runtimes.server.app",
    "create_server_app": "palm.common.runtimes.server.app",
    "ServerContext": "palm.common.runtimes.server.context",
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
    "ServerApp",
    "ServerContext",
    "ServerRequest",
    "ServerResponse",
    "ServerSurface",
    "ServerWebhookBridge",
    "SurfaceRegistry",
    "TransportRegistry",
    "authenticate_request",
    "create_server_app",
    "current_principal_id",
    "error_response",
    "transport_registry",
]
