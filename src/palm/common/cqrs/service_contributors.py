"""Service-domain CQRS contributor registry — transport wiring at bootstrap."""

from __future__ import annotations

import threading
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

WireFn = Callable[[Any, Any, Any], None]


@dataclass(frozen=True)
class ServiceCqrsContributor:
    """Service-owned CQRS command/query types and bus wiring hook."""

    service_name: str
    command_types: tuple[type, ...] = ()
    query_types: tuple[type, ...] = ()
    command_schemas: dict[type, Any] = field(default_factory=dict, compare=False, hash=False)
    query_schemas: dict[type, Any] = field(default_factory=dict, compare=False, hash=False)
    wire: WireFn | None = None


_lock = threading.RLock()
_contributors: dict[str, ServiceCqrsContributor] = {}


def register_service_cqrs_contributor(contributor: ServiceCqrsContributor) -> None:
    """Register a service CQRS contributor (thread-safe, bootstrap time)."""
    with _lock:
        existing = _contributors.get(contributor.service_name)
        if existing is contributor:
            return
        _contributors[contributor.service_name] = contributor


def iter_service_cqrs_contributors() -> tuple[ServiceCqrsContributor, ...]:
    with _lock:
        return tuple(_contributors.values())


def clear_service_cqrs_contributors() -> None:
    """Remove service CQRS registrations (primarily for tests)."""
    with _lock:
        _contributors.clear()


def wire_service_cqrs_contributors(
    command_bus: Any,
    query_bus: Any,
    contexts: dict[str, Any],
) -> None:
    """Drain registered contributors and invoke each ``wire`` hook."""
    for contributor in iter_service_cqrs_contributors():
        if contributor.wire is None:
            continue
        context = contexts.get(contributor.service_name)
        if context is None:
            continue
        contributor.wire(command_bus, query_bus, context)


__all__ = [
    "ServiceCqrsContributor",
    "clear_service_cqrs_contributors",
    "iter_service_cqrs_contributors",
    "register_service_cqrs_contributor",
    "wire_service_cqrs_contributors",
]