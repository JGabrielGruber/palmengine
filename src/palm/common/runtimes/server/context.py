"""
ServerContext — bridges runtimes, ApplicationHost, and CQRS buses.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from palm.common.cqrs.bus import CommandBus, QueryBus
from palm.common.cqrs.command import Command
from palm.common.cqrs.query import Query
from palm.common.plans import PlanRegistry
from palm.common.runtimes.server.cqrs import wire_standalone_buses

if TYPE_CHECKING:
    from palm.app.host.application_host import ApplicationHost
    from palm.common.runtimes.base import BaseRuntime


class ServerContext:
    """
    Shared execution context for all server surfaces.

    When an :class:`~palm.app.host.ApplicationHost` is attached, commands and
    queries flow through the host buses (projections, routing, webhooks). In
    standalone :class:`~palm.runtimes.server.runtime.ServerRuntime` mode, local
    buses are wired directly to the hosting runtime.
    """

    def __init__(
        self,
        runtime: BaseRuntime,
        *,
        host: ApplicationHost | None = None,
        plan_registry: PlanRegistry | None = None,
    ) -> None:
        self._runtime = runtime
        self._host = host
        self.plan_registry = plan_registry or PlanRegistry()
        self._command_bus = host.commands if host is not None else CommandBus()
        self._query_bus = host.queries if host is not None else QueryBus()
        if host is None:
            wire_standalone_buses(
                self._command_bus,
                self._query_bus,
                runtime,
                plan_registry=self.plan_registry,
            )

    @property
    def runtime(self) -> BaseRuntime:
        return self._runtime

    @property
    def host(self) -> ApplicationHost | None:
        return self._host

    @property
    def command_bus(self) -> CommandBus:
        return self._command_bus

    @property
    def query_bus(self) -> QueryBus:
        return self._query_bus

    def execute(self, command: Command) -> Any:
        return self._command_bus.dispatch(command)

    def ask(self, query: Query) -> Any:
        return self._query_bus.ask(query)

    def wait_until_idle(self, *, timeout: float = 5.0) -> bool:
        return self._runtime.wait_until_idle(timeout=timeout)

    def attach_host(self, host: ApplicationHost) -> None:
        """Switch command/query dispatch to an ApplicationHost after CQRS wiring."""
        self._host = host
        self._command_bus = host.commands
        self._query_bus = host.queries