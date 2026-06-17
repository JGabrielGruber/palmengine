"""Network-hosted Palm runtime with extensible server surfaces."""

from palm.common.runtimes.server import (
    BaseSurface,
    BaseTransport,
    PALM_SUBJECT_HEADER,
    RouteRegistry,
    ServerApp,
    ServerContext,
    SurfaceRegistry,
    TransportRegistry,
    create_server_app,
    transport_registry,
)
from palm.runtimes.server.auth import authenticate_request
from palm.runtimes.server.factory import build_server_context, create_app
from palm.runtimes.server.runtime import ServerRuntime, run_server
from palm.runtimes.server.surfaces import (
    ExplorerSurface,
    McpSurface,
    RestSurface,
    SsrSurface,
    WebSocketSurface,
    default_surfaces,
)
from palm.runtimes.server.transport import DEFAULT_TRANSPORT, StdlibHttpTransport, create_transport

__all__ = [
    "DEFAULT_TRANSPORT",
    "BaseSurface",
    "BaseTransport",
    "ExplorerSurface",
    "McpSurface",
    "PALM_SUBJECT_HEADER",
    "RestSurface",
    "RouteRegistry",
    "ServerApp",
    "ServerContext",
    "ServerRuntime",
    "SsrSurface",
    "StdlibHttpTransport",
    "SurfaceRegistry",
    "TransportRegistry",
    "WebSocketSurface",
    "authenticate_request",
    "build_server_context",
    "create_app",
    "create_server_app",
    "create_transport",
    "default_surfaces",
    "run_server",
    "transport_registry",
]