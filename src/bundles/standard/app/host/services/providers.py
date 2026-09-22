"""
Core host service providers (T2 / 0.48.2).

Core services and their construction, declared as dependency-ordered
``ServiceProvider`` entries. The host builds them via
``HostServiceRegistry.build_all(ctx)``.

Construction order encoded by ``depends_on``:
``inspect`` → ``session`` → ``definitions`` → ``execution`` →
``assist``/``design``/``analytics``.
The ``assist.bind_analytics(analytics)`` cross-wire is a shared post-build
packaging step (:func:`~palm.app.host.services.packaging.apply_product_packaging`),
not a construction dependency — both host and host-less ServerContext call it.

**0.58.12:** product ``session`` is the surface door over the system session plane.
**0.61.4 / SD-007:** product inspect door is ``inspect`` (was ``system``).
"""

from __future__ import annotations

from typing import Any

from bundles.standard.app.host.services.registry import HostServiceContext, HostServiceRegistry, ServiceProvider


def _build_inspect(ctx: HostServiceContext, built: dict[str, Any]) -> Any:
    from palm.services.inspect import InspectService

    return InspectService(**ctx.bus_kwargs)


def _build_session(ctx: HostServiceContext, built: dict[str, Any]) -> Any:
    from palm.services.session import SessionService

    return SessionService(
        **ctx.bus_kwargs,
        inspect=built["inspect"],
        runtime_resolver=ctx.resolve_execution_runtime,
        strict_attribution=bool(
            getattr(ctx.settings, "session_strict_attribution", True)
        ),
    )


def _build_definitions(ctx: HostServiceContext, built: dict[str, Any]) -> Any:
    from palm.services.definitions import DefinitionService

    return DefinitionService(**ctx.bus_kwargs, repository=ctx.app.repository())


def _build_execution(ctx: HostServiceContext, built: dict[str, Any]) -> Any:
    # 0.63.30/31 — inject published admission for execution product façades.
    from palm.services.execution import ExecutionService
    from palm.services.execution.flows import FlowExecutionService
    from palm.services.execution.processes import ProcessExecutionService
    from palm.services.execution.providers import ProviderExecutionService
    from palm.services.execution.workloads import WorkloadExecutionService
    from palm.system.structure.access import admission_source_from_runtime_resolver

    admission_source = admission_source_from_runtime_resolver(
        ctx.resolve_execution_runtime
    )
    flows = FlowExecutionService(
        **ctx.bus_kwargs,
        inspect=built["inspect"],
        session=built.get("session"),
        runtime_resolver=ctx.resolve_execution_runtime,
        admission_source=admission_source,
    )
    providers = ProviderExecutionService(
        **ctx.bus_kwargs,
        runtime_resolver=ctx.resolve_execution_runtime,
        definitions=built["definitions"],
        event_engine=ctx.event,
        admission_source=admission_source,
    )
    processes = ProcessExecutionService(
        **ctx.bus_kwargs,
        runtime_resolver=ctx.resolve_execution_runtime,
        admission_source=admission_source,
    )
    workloads = WorkloadExecutionService(
        **ctx.bus_kwargs,
        runtime_resolver=ctx.resolve_execution_runtime,
        admission_source=admission_source,
    )
    return ExecutionService(
        flows=flows,
        providers=providers,
        processes=processes,
        workloads=workloads,
    )


def _build_assist(ctx: HostServiceContext, built: dict[str, Any]) -> Any:
    # 0.63.22/23 — inject published admission; packaging binds it once.
    from palm.services.assist import AssistService
    from palm.system.structure.access import admission_source_from_runtime_resolver

    return AssistService(
        **ctx.bus_kwargs,
        definitions=built["definitions"],
        execution=built["execution"],
        inspect=built["inspect"],
        session=built.get("session"),
        runtime_resolver=ctx.resolve_execution_runtime,
        admission_source=admission_source_from_runtime_resolver(
            ctx.resolve_execution_runtime
        ),
    )


def _build_design(ctx: HostServiceContext, built: dict[str, Any]) -> Any:
    from palm.services.design import DesignService
    from palm.services.design.factory import create_proposal_repository

    return DesignService(
        **ctx.bus_kwargs,
        definitions=built["definitions"],
        proposals=create_proposal_repository(ctx.app.storage),
        runtime_resolver=ctx.resolve_execution_runtime,
    )


def _build_analytics(ctx: HostServiceContext, built: dict[str, Any]) -> Any:
    from palm.services.analytics import AnalyticsService

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
    ServiceProvider("inspect", _build_inspect),
    ServiceProvider("session", _build_session, depends_on=("inspect",)),
    ServiceProvider("definitions", _build_definitions),
    ServiceProvider(
        "execution",
        _build_execution,
        depends_on=("inspect", "definitions", "session"),
    ),
    ServiceProvider(
        "assist",
        _build_assist,
        depends_on=("definitions", "execution", "inspect", "session"),
    ),
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
