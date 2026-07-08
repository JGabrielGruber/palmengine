"""
ServerContext — bridges runtimes, ApplicationHost, and CQRS buses.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from palm.common.cqrs.bus import CommandBus, QueryBus
from palm.common.cqrs.command import Command
from palm.common.cqrs.query import Query
from palm.common.cqrs.schemas import CqrsSchemaRegistry, build_schema_registry
from palm.common.plans import PlanRegistry
from palm.common.runtimes.server.cqrs import wire_standalone_buses
from palm.services.assist import AssistService
from palm.services.definitions import DefinitionService
from palm.services.design import DesignService
from palm.services.design.factory import create_proposal_repository
from palm.services.execution import ExecutionService
from palm.services.execution.flows import FlowExecutionService
from palm.services.execution.processes import ProcessExecutionService
from palm.services.execution.providers import ProviderExecutionService
from palm.services.system import SystemService

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
            schemas = build_schema_registry()
            bus_kw = {
                "commands": self._command_bus,
                "queries": self._query_bus,
                "schemas": schemas,
            }
            self._system = SystemService(**bus_kw)
            self._definitions = DefinitionService(
                **bus_kw,
                repository=runtime.repository,
            )
            flows = FlowExecutionService(**bus_kw, system=self._system, runtime=runtime)
            definitions = self._definitions
            self._execution = ExecutionService(
                flows=flows,
                providers=ProviderExecutionService(
                    **bus_kw,
                    runtime=runtime,
                    definitions=definitions,
                ),
                processes=ProcessExecutionService(**bus_kw, runtime=runtime),
            )
            self._assist = AssistService(
                **bus_kw,
                definitions=definitions,
                execution=self._execution,
                system=self._system,
                runtime=runtime,
            )
            self._design = DesignService(
                **bus_kw,
                definitions=definitions,
                proposals=create_proposal_repository(runtime.storage),
                runtime=runtime,
            )
            from palm.services._cqrs_wiring import wire_all_service_cqrs_from_runtime
            from palm.services.design.contributors import wire_builtin_design_contributors

            wire_builtin_design_contributors()
            wire_all_service_cqrs_from_runtime(
                self._command_bus,
                self._query_bus,
                runtime,
                design=self._design,
            )
        else:
            self._system = host.system
            self._definitions = host.definitions
            self._execution = host.execution
            self._assist = host.assist
            self._design = host.design

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

    @property
    def schemas(self) -> CqrsSchemaRegistry:
        if self._host is not None:
            return self._host.schemas
        return self._system.schemas

    @property
    def system(self) -> SystemService:
        if self._host is not None:
            return self._host.system
        return self._system

    @property
    def definitions(self) -> DefinitionService:
        if self._host is not None:
            return self._host.definitions
        return self._definitions

    @property
    def execution(self) -> ExecutionService:
        if self._host is not None:
            return self._host.execution
        return self._execution

    @property
    def assist(self) -> AssistService:
        if self._host is not None:
            return self._host.assist
        return self._assist

    @property
    def design(self) -> DesignService:
        if self._host is not None:
            return self._host.design
        return self._design

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
        self._system = host.system
        self._definitions = host.definitions
        self._execution = host.execution
        self._assist = host.assist
        self._design = host.design