"""Shared server infrastructure — protocol, routing, transport, and CQRS bridging."""

from palm.common.runtimes.server.app import ServerApp, create_server_app
from palm.common.runtimes.server.context import ServerContext
from palm.common.runtimes.server.middleware import (
    PALM_SUBJECT_HEADER,
    authenticate_request,
    current_principal_id,
)
from palm.common.runtimes.server.protocol import HttpMethod, ServerRequest, ServerResponse, ServerSurface
from palm.common.runtimes.server.registry import RouteRegistry, RouteSpec, SurfaceRegistry
from palm.common.runtimes.server.responses import error_response
from palm.common.runtimes.server.surface import BaseSurface
from palm.common.runtimes.server.transport import BaseTransport, TransportRegistry, transport_registry
from palm.common.runtimes.server.webhooks import ServerWebhookBridge

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