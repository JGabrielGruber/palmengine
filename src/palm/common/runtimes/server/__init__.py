"""Shared server infrastructure — surfaces, routing, and CQRS bridging."""

from palm.common.runtimes.server.app import ServerApp, create_server_app, default_surfaces
from palm.common.runtimes.server.context import ServerContext
from palm.common.runtimes.server.middleware import (
    PALM_SUBJECT_HEADER,
    authenticate_request,
    current_principal_id,
)
from palm.common.runtimes.server.protocol import HttpMethod, ServerRequest, ServerResponse, ServerSurface
from palm.common.runtimes.server.registry import RouteRegistry, RouteSpec, SurfaceRegistry
from palm.common.runtimes.server.surfaces.rest import RestSurface
from palm.common.runtimes.server.webhooks import ServerWebhookBridge

__all__ = [
    "HttpMethod",
    "PALM_SUBJECT_HEADER",
    "RestSurface",
    "RouteRegistry",
    "RouteSpec",
    "ServerApp",
    "ServerContext",
    "ServerRequest",
    "ServerResponse",
    "ServerSurface",
    "ServerWebhookBridge",
    "SurfaceRegistry",
    "authenticate_request",
    "create_server_app",
    "current_principal_id",
    "default_surfaces",
]