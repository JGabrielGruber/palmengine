"""
Server registries — thread-safe route and surface registration.
"""

from __future__ import annotations

import re
import threading
from collections.abc import Iterable
from dataclasses import dataclass
from typing import TYPE_CHECKING

from palm.core.exceptions import RegistryError

if TYPE_CHECKING:
    from palm.common.runtimes.server.protocol import RouteHandler, ServerSurface


@dataclass(frozen=True)
class RouteSpec:
    """A single route binding on a server surface."""

    method: str
    pattern: re.Pattern[str]
    handler: RouteHandler
    surface: str
    auth_required: bool = False
    raw_path: str = ""


class RouteRegistry:
    """Thread-safe HTTP-style route table with regex path matching."""

    def __init__(self) -> None:
        self._routes: list[RouteSpec] = []
        self._lock = threading.RLock()

    def register(
        self,
        *,
        method: str,
        path: str,
        handler: RouteHandler,
        surface: str,
        auth_required: bool = False,
    ) -> None:
        normalized = _normalize_path(path)
        pattern = re.compile("^" + _path_to_regex(normalized) + "$")
        spec = RouteSpec(
            method=method.upper(),
            pattern=pattern,
            handler=handler,
            surface=surface,
            auth_required=auth_required,
            raw_path=normalized,
        )
        with self._lock:
            self._routes.append(spec)

    def match(self, method: str, path: str) -> RouteSpec | None:
        normalized = _normalize_path(path)
        verb = method.upper()
        with self._lock:
            for spec in self._routes:
                if spec.method == verb and spec.pattern.match(normalized):
                    return spec
        return None

    def routes(self) -> tuple[RouteSpec, ...]:
        with self._lock:
            return tuple(self._routes)

    def clear(self) -> None:
        with self._lock:
            self._routes.clear()


class SurfaceRegistry:
    """Thread-safe registry of :class:`~palm.common.runtimes.server.protocol.ServerSurface` implementations."""

    def __init__(self) -> None:
        self._entries: dict[str, ServerSurface] = {}
        self._lock = threading.RLock()

    def register(self, surface: ServerSurface) -> None:
        with self._lock:
            self._entries[surface.name] = surface

    def get(self, name: str) -> ServerSurface:
        with self._lock:
            try:
                return self._entries[name]
            except KeyError as exc:
                available = sorted(self._entries)
                raise RegistryError(
                    f"Unknown server surface {name!r}. Available: {available}"
                ) from exc

    def names(self) -> list[str]:
        with self._lock:
            return sorted(self._entries)

    def all(self) -> Iterable[ServerSurface]:
        with self._lock:
            return tuple(self._entries.values())

    def clear(self) -> None:
        with self._lock:
            self._entries.clear()


def _normalize_path(path: str) -> str:
    if not path.startswith("/"):
        path = f"/{path}"
    if len(path) > 1 and path.endswith("/"):
        path = path.rstrip("/")
    return path


def _path_to_regex(path: str) -> str:
    parts: list[str] = []
    for segment in path.split("/"):
        if not segment:
            continue
        if segment.startswith("{") and segment.endswith("}"):
            name = segment[1:-1]
            parts.append(f"(?P<{name}>[^/]+)")
        else:
            parts.append(re.escape(segment))
    return "/" + "/".join(parts) if parts else "/"
