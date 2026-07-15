"""
Core host service providers (T2 / 0.48.2).

The six core services and their construction, declared as dependency-ordered
``ServiceProvider`` entries. Extracted verbatim (behaviour-preserving) from
``ApplicationHost._wire_cqrs``; the host now builds them via
``HostServiceRegistry.build_all(ctx)``.

Construction order encoded by ``depends_on``:
``system``/``definitions`` → ``execution`` → ``assist``/``design``/``analytics``.
The ``assist.bind_analytics(analytics)`` cross-wire stays an explicit host
post-build step (a mutual link, not a construction dependency).
"""

from __future__ import annotations

from typing import Any

from palm.app.host.services.registry import HostServiceContext, HostServiceRegistry, ServiceProvider
from palm.services.analytics import AnalyticsService
from palm.services.assist import AssistService
from palm.services.definitions import DefinitionService
from palm.services.design import DesignService
from palm.services.design.factory import create_proposal_repository
from palm.services.execution import ExecutionService
from palm.services.execution.flows import FlowExecutionService
from palm.services.execution.processes import ProcessExecutionService
from palm.services.execution.providers import ProviderExecutionService
from palm.services.system import SystemService


def _build_system(ctx: HostServiceContext, built: dict[str, Any]) -> Any:
    return SystemService(**ctx.bus_kwargs)


def _build_definitions(ctx: HostServiceContext, built: dict[str, Any]) -> Any:
    return DefinitionService(**ctx.bus_kwargs, repository=ctx.app.repository())


def _build_execution(ctx: HostServiceContext, built: dict[str, Any]) -> Any:
    flows = FlowExecutionService(
        **ctx.bus_kwargs,
        system=built["system"],
        runtime_resolver=ctx.resolve_execution_runtime,
    )
    providers = ProviderExecutionService(
        **ctx.bus_kwargs,
        runtime_resolver=ctx.resolve_execution_runtime,
        definitions=built["definitions"],
        event_engine=ctx.event,
    )
    processes = ProcessExecutionService(
        **ctx.bus_kwargs,
        runtime_resolver=ctx.resolve_execution_runtime,
    )
    return ExecutionService(flows=flows, providers=providers, processes=processes)


def _build_assist(ctx: HostServiceContext, built: dict[str, Any]) -> Any:
    return AssistService(
        **ctx.bus_kwargs,
        definitions=built["definitions"],
        execution=built["execution"],
        system=built["system"],
        runtime_resolver=ctx.resolve_execution_runtime,
    )


def _build_design(ctx: HostServiceContext, built: dict[str, Any]) -> Any:
    return DesignService(
        **ctx.bus_kwargs,
        definitions=built["definitions"],
        proposals=create_proposal_repository(ctx.app.storage),
        runtime_resolver=ctx.resolve_execution_runtime,
    )


def _build_analytics(ctx: HostServiceContext, built: dict[str, Any]) -> Any:
    settings = ctx.settings
    allow_unpub = bool(settings.analytics_allow_unpublished)
    if settings.analytics_allow_unpublished_with_server:
        allow_unpub = True
    return AnalyticsService(
        definitions=built["definitions"],
        providers=built["execution"].providers,
        commands=ctx.command_bus,
        queries=ctx.query_bus,
        schemas=ctx.schemas,
        allow_unpublished=allow_unpub,
        default_limit=int(settings.analytics_default_limit),
        max_limit=int(settings.analytics_max_limit),
        max_response_bytes=int(settings.analytics_max_response_bytes),
        enabled=bool(settings.analytics_enabled),
    )


CORE_SERVICE_PROVIDERS: tuple[ServiceProvider, ...] = (
    ServiceProvider("system", _build_system),
    ServiceProvider("definitions", _build_definitions),
    ServiceProvider("execution", _build_execution, depends_on=("system", "definitions")),
    ServiceProvider("assist", _build_assist, depends_on=("definitions", "execution", "system")),
    ServiceProvider("design", _build_design, depends_on=("definitions",)),
    ServiceProvider("analytics", _build_analytics, depends_on=("definitions", "execution")),
)


def core_service_registry() -> HostServiceRegistry:
    """A fresh registry pre-loaded with the core host service providers."""
    registry = HostServiceRegistry()
    for provider in CORE_SERVICE_PROVIDERS:
        registry.register(provider)
    return registry


__all__ = ["CORE_SERVICE_PROVIDERS", "core_service_registry"]
