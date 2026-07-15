"""
HostServiceRegistry — typed, dependency-ordered construction of host services (T2 / 0.48.2, PD-009).

Replaces the imperative service-construction block in ``ApplicationHost._wire_cqrs``
with declarative providers: each service declares what it depends on, and
``build_all(ctx)`` constructs them in topological order. This is the same
register-and-drain shape T3 established (``common/cqrs/service_contributors`` et al.),
applied to service *construction*.

Public API is unchanged — the host still exposes ``host.system``/``host.execution``/…
as thin accessors over the slots this registry fills.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from palm.app.app import PalmApp
    from palm.app.settings import PalmSettings
    from palm.common.cqrs.bus import CommandBus, QueryBus
    from palm.core.event import EventEngine
    from palm.runtimes.base import BaseRuntime


@dataclass(frozen=True)
class HostServiceContext:
    """Everything a service provider needs to build its service."""

    command_bus: CommandBus
    query_bus: QueryBus
    schemas: Any
    app: PalmApp
    event: EventEngine
    settings: PalmSettings
    resolve_execution_runtime: Callable[[str | None], BaseRuntime]

    @property
    def bus_kwargs(self) -> dict[str, Any]:
        """The ``commands``/``queries``/``schemas`` trio most services take."""
        return {"commands": self.command_bus, "queries": self.query_bus, "schemas": self.schemas}


BuildFn = Callable[[HostServiceContext, dict[str, Any]], Any]


@dataclass(frozen=True)
class ServiceProvider:
    """A named host service and the services it must be built after."""

    name: str
    build: BuildFn
    depends_on: tuple[str, ...] = ()


@dataclass
class HostServiceRegistry:
    """Registry of service providers, built in dependency order."""

    _providers: dict[str, ServiceProvider] = field(default_factory=dict)
    _order: list[str] = field(default_factory=list)

    def register(self, provider: ServiceProvider) -> None:
        if provider.name not in self._providers:
            self._order.append(provider.name)
        self._providers[provider.name] = provider

    def build_all(self, ctx: HostServiceContext) -> dict[str, Any]:
        """Construct every registered service in dependency order.

        Returns a ``{name: service}`` map. Raises on an unknown or cyclic
        dependency rather than building a partial graph.
        """
        built: dict[str, Any] = {}
        pending = list(self._order)
        while pending:
            progressed = False
            for name in list(pending):
                provider = self._providers[name]
                unmet = [d for d in provider.depends_on if d not in built]
                if any(d not in self._providers for d in provider.depends_on):
                    missing = [d for d in provider.depends_on if d not in self._providers]
                    raise ValueError(f"service {name!r} depends on unregistered {missing}")
                if unmet:
                    continue
                built[name] = provider.build(ctx, built)
                pending.remove(name)
                progressed = True
            if not progressed:
                raise ValueError(f"cyclic or unresolvable service dependencies among {pending}")
        return built


__all__ = [
    "BuildFn",
    "HostServiceContext",
    "HostServiceRegistry",
    "ServiceProvider",
]
