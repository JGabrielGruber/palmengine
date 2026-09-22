"""
Transport contract — what a wire binding may call, and how it is registered.

The kit owns this expectation. A composition root implements
:class:`TransportApp` and registers a factory. The bundled server runtime is
one such root.
"""

from __future__ import annotations

import threading
from collections.abc import Callable
from typing import Protocol, runtime_checkable

from palm.core.exceptions import RegistryError
from plugins.kits.server.protocol import ServerRequest, ServerResponse

TransportFactory = Callable[["TransportApp", str, int], "BaseTransport"]


@runtime_checkable
class TransportApp(Protocol):
    """What a transport is allowed to call on the mounted application.

    Accept a normalized request and return a normalized response, sync or async.
    The composition root decides how routes, auth, and surfaces are wired.
    """

    def dispatch(self, request: ServerRequest) -> ServerResponse:
        """Run the sync dispatch path."""

    async def dispatch_async(self, request: ServerRequest) -> ServerResponse:
        """Run the async dispatch path."""


@runtime_checkable
class BaseTransport(Protocol):
    """
    Binds a :class:`TransportApp` to a wire protocol.

    Implementations may be sync (stdlib HTTP) or async (Starlette/uvicorn). Async
    transports serve every HTTP-mounted surface and upgrade path (WebSocket)
    through :meth:`TransportApp.dispatch_async`.
    """

    @property
    def name(self) -> str:
        """Registry name (e.g. ``stdlib``, ``starlette``)."""

    @property
    def host(self) -> str:
        """Bound host address."""

    @property
    def port(self) -> int:
        """Bound port."""

    def start(self, *, blocking: bool = False) -> None:
        """Begin accepting connections."""

    def stop(self) -> None:
        """Shut down the transport."""


class TransportRegistry:
    """Thread-safe registry of named transport factories."""

    def __init__(self) -> None:
        self._entries: dict[str, TransportFactory] = {}
        self._lock = threading.RLock()

    def register(self, name: str, factory: TransportFactory) -> None:
        with self._lock:
            self._entries[name] = factory

    def create(
        self,
        name: str,
        app: TransportApp,
        *,
        host: str,
        port: int,
    ) -> BaseTransport:
        with self._lock:
            try:
                factory = self._entries[name]
            except KeyError as exc:
                available = sorted(self._entries)
                raise RegistryError(
                    f"Unknown server transport {name!r}. Available: {available}"
                ) from exc
        return factory(app, host, port)

    def names(self) -> list[str]:
        with self._lock:
            return sorted(self._entries)

    def clear(self) -> None:
        with self._lock:
            self._entries.clear()


transport_registry = TransportRegistry()
