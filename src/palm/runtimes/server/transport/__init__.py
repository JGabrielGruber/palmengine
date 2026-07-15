"""Server transports — pluggable wire bindings."""

from __future__ import annotations

from typing import TYPE_CHECKING

from palm.common.runtimes.server.transport import BaseTransport, transport_registry
from palm.runtimes.server.transport.stdlib import (
    StdlibHttpTransport,
    create_stdlib_transport,
    serve_app,
)

if TYPE_CHECKING:
    from palm.runtimes.server.app import ServerApp

DEFAULT_TRANSPORT = "stdlib"

transport_registry.register(DEFAULT_TRANSPORT, create_stdlib_transport)


def create_transport(
    name: str,
    app: ServerApp,
    *,
    host: str,
    port: int,
) -> BaseTransport:
    """Instantiate a registered transport by name."""
    return transport_registry.create(name, app, host=host, port=port)


__all__ = [
    "DEFAULT_TRANSPORT",
    "BaseTransport",
    "StdlibHttpTransport",
    "create_transport",
    "serve_app",
    "transport_registry",
]
