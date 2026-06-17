"""
Transport protocol — pluggable wire bindings for :class:`~palm.common.runtimes.server.app.ServerApp`.
"""

from __future__ import annotations

import threading
from collections.abc import Callable
from typing import TYPE_CHECKING, Protocol, runtime_checkable

from palm.core.exceptions import RegistryError

if TYPE_CHECKING:
    from palm.common.runtimes.server.app import ServerApp

TransportFactory = Callable[["ServerApp", str, int], "BaseTransport"]


@runtime_checkable
class BaseTransport(Protocol):
    """
    Binds a :class:`~palm.common.runtimes.server.app.ServerApp` to a wire protocol.

    Implementations may be sync (stdlib HTTP) or async (Starlette/uvicorn). Async
    transports should serve all HTTP-mounted surfaces and upgrade paths (WebSocket).
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
        app: ServerApp,
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
