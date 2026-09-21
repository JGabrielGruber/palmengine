"""
ServerContext — surface-facing single-runtime view + lean composition root.

Retained as a type (ADR-019 / scout 0.51.6): surfaces need ``ctx.runtime`` as a
property; ApplicationHost keeps multi-runtime ``runtime(name)``. Product services
build through the same ``core_service_registry`` + shared packaging helper.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from palm.app.host.composition import CompositionProfile, composition_profile_from_name
from palm.app.host.services import (
    HostServiceContext,
    apply_product_packaging,
    core_service_registry,
)
from palm.app.settings import PalmSettings
from palm.common.cqrs.bus import CommandBus, QueryBus
from palm.common.cqrs.command import Command
from palm.common.cqrs.query import Query
from palm.common.cqrs.schemas import CqrsSchemaRegistry, build_schema_registry
from palm.common.plans import PlanRegistry
from palm.kits.server.cqrs import wire_standalone_buses

if TYPE_CHECKING:
    from palm.app.host.application_host import ApplicationHost
    from palm.services.analytics import AnalyticsService
    from palm.services.assist import AssistService
    from palm.services.definitions import DefinitionService
    from palm.services.design import DesignService
    from palm.services.execution import ExecutionService
    from palm.services.inspect import InspectService
    from palm.services.session import SessionService
    from palm.system.runtime.base import BaseRuntime


class _RuntimeKernelView:
    """The kernel shape the service providers build against, over one runtime.

    ApplicationHost passes its :class:`~palm.app.kernel.PalmKernel` as
    ``HostServiceContext.app``; a host-less ``ServerContext`` has only its single
    runtime. This thin view presents the two members the providers touch —
    ``repository()`` and ``storage`` — so both composition roots can construct
    services through the same ``core_service_registry()`` (0.50.5e). It is the
    bridge the runtime↔kernel seam (0.50.5c) pointed toward.
    """

    __slots__ = ("_runtime",)

    def __init__(self, runtime: BaseRuntime) -> None:
        self._runtime = runtime

    def repository(self, *, runtime_name: str | None = None) -> Any:
        return self._runtime.repository

    @property
    def storage(self) -> Any:
        return self._runtime.storage


class ServerContext:
    """
    The server composition root — and the surface-facing context every surface programs against.

    ``ServerContext`` is two things at once:

    1. **The surface-facing context.** Every REST / WebSocket / MCP / SSR handler
       and route takes a ``ctx: ServerContext`` and reads through its uniform
       surface (``ask``/``execute``/``execution``/``definitions``/``composition``/…),
       independent of what is assembling behind it.
    2. **The lean server composition root.** When no host is attached it *is* the
       saved ``server`` composition record — a single :class:`ServerRuntime`,
       no projection layer, reads served directly from the runtime
       (``wire_standalone_buses``). It is the server-side sibling of
       the saved ``embedded`` record: one genome, a leaner phenotype.

    Services build through the **same** ``core_service_registry()`` and shared
    :func:`~palm.app.host.services.packaging.apply_product_packaging` as
    :class:`~palm.app.host.application_host.ApplicationHost` (BI-003 packaging
    residual). What stays distinct is *dispatch phenotype*: an attached host
    routes through projection-ful buses; host-less, local buses serve reads live
    from the runtime. The type is **retained** (ADR-019 · scout 0.51.6) — dual
    *types* for host vs surface view; one *structure law* for product services.
    """

    def __init__(
        self,
        runtime: BaseRuntime,
        *,
        host: ApplicationHost | None = None,
        plan_registry: PlanRegistry | None = None,
        settings: PalmSettings | None = None,
    ) -> None:
        self._runtime = runtime
        self._host = host
        self._settings = settings if settings is not None else PalmSettings()
        self.plan_registry = plan_registry or PlanRegistry()
        self._command_bus = host.commands if host is not None else CommandBus()
        self._query_bus = host.queries if host is not None else QueryBus()
        if host is None:
            self._build_standalone_services(runtime)
        else:
            self._inspect = host.inspect
            self._session = host.session
            self._definitions = host.definitions
            self._execution = host.execution
            self._assist = host.assist
            self._design = host.design
            self._analytics = host.analytics

    def _build_standalone_services(self, runtime: BaseRuntime) -> None:
        """Construct and wire services for standalone (host-less) server mode.

        Same ``core_service_registry`` + product packaging as ApplicationHost.
        ``event=None`` keeps host-less providers from emitting (no standalone
        coordination event plane). Settings come from the constructor (or
        default :class:`PalmSettings`) so MCP/bootstrap config is not silent.
        """
        wire_standalone_buses(
            self._command_bus,
            self._query_bus,
            runtime,
            plan_registry=self.plan_registry,
        )
        service_ctx = HostServiceContext(
            command_bus=self._command_bus,
            query_bus=self._query_bus,
            schemas=build_schema_registry(),
            app=_RuntimeKernelView(runtime),
            event=None,
            settings=self._settings,
            resolve_execution_runtime=self.resolve_execution_runtime,
        )
        from palm.services._apps import autoload as autoload_services

        autoload_services(tuple(self.composition.services))
        built = core_service_registry().build_all(service_ctx, only=self.composition.services)
        bag = apply_product_packaging(
            built,
            command_bus=self._command_bus,
            query_bus=self._query_bus,
            repository=runtime.repository,
            instance_manager=runtime.instance_manager,
            storage=getattr(runtime, "storage", None),
        )
        self._inspect = bag.inspect
        self._session = bag.session
        self._definitions = bag.definitions
        self._execution = bag.execution
        self._assist = bag.assist
        self._design = bag.design
        self._analytics = bag.analytics

    @property
    def runtime(self) -> BaseRuntime:
        return self._runtime

    @property
    def host(self) -> ApplicationHost | None:
        return self._host

    @property
    def settings(self) -> PalmSettings:
        """Settings used for standalone service build (host path uses ``host.settings``)."""
        if self._host is not None:
            return self._host.settings
        return self._settings

    @property
    def composition(self) -> CompositionProfile:
        """What this server context is composed of.

        An attached host contributes its ``CompositionProfile``; standalone, the
        server context *is* the server shape. Both roots speak the same
        ``composition`` language (0.50.5+); the type stays as the surface view.
        """
        return (
            self._host.composition
            if self._host is not None
            else composition_profile_from_name("server")
        )

    def resolve_execution_runtime(self, runtime_name: str | None = None) -> BaseRuntime:
        """Runtime services execute on — host routes by name; standalone is this runtime."""
        if self._host is not None:
            return self._host._resolve_execution_runtime(runtime_name)
        return self._runtime

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
        return self._inspect.schemas

    @property
    def inspect(self) -> InspectService:
        """Product inspect door (0.61.4 / SD-007)."""
        if self._host is not None:
            return self._host.inspect
        return self._inspect

    @property
    def system(self) -> InspectService:
        """Deprecated alias for :attr:`inspect` (SD-007 migration)."""
        return self.inspect

    @property
    def session(self) -> SessionService | None:
        """Product session door (0.58.12) when composed."""
        if self._host is not None:
            return self._host.session
        return getattr(self, "_session", None)

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

    @property
    def analytics(self) -> AnalyticsService:
        if self._host is not None:
            return self._host.analytics
        return self._analytics

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
        self._inspect = host.inspect
        self._session = host.session
        self._definitions = host.definitions
        self._execution = host.execution
        self._assist = host.assist
        self._design = host.design
        self._analytics = host.analytics
