"""The type catalog reads the system registry (0.72.17).

``collect_cqrs_command_types`` and ``collect_cqrs_query_types`` copy pattern
command types and query types from the ``cqrs_contributor`` table the caller
passes. A missing pattern name is not copied from the process list. A runtime
that does not install the table does not read that list. Service types stay
on the process service list.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import pytest
from bundles.minimal.bind import bind_memory
from bundles.minimal.runtime import MinimalRuntime
from plugins.patterns.wizard.bindings.cqrs.contributor import wizard_cqrs_contributor
from plugins.patterns.wizard.registry import register as register_wizard

from palm.common.cqrs.bus import CommandBus, QueryBus
from palm.common.cqrs.catalog import (
    CatalogMode,
    collect_cqrs_command_types,
    collect_cqrs_query_types,
)
from palm.common.cqrs.command import Command, SubmitFlowCommand
from palm.common.cqrs.query import GetResourceInvocationsQuery, Query
from palm.common.cqrs.service_contributors import (
    ServiceCqrsContributor,
    register_service_cqrs_contributor,
)
from palm.common.cqrs.standalone import wire_standalone_buses, wire_standalone_query_bus
from palm.common.patterns._registry import (
    CqrsContributor,
    get_cqrs_contributor,
    register_cqrs_contributor,
)
from palm.common.plans.registry import PlanRegistry
from palm.core.exceptions import RegistryError
from palm.core.registry import Registry


@dataclass(frozen=True)
class _CommandA(Command):
    pass


@dataclass(frozen=True)
class _CommandB(Command):
    pass


@dataclass(frozen=True)
class _ProcessCommand(Command):
    pass


@dataclass(frozen=True)
class _ServiceCommand(Command):
    slug: str = ""


@dataclass(frozen=True)
class _QueryA(Query):
    pass


@dataclass(frozen=True)
class _QueryB(Query):
    pass


@dataclass(frozen=True)
class _ProcessQuery(Query):
    pass


@dataclass(frozen=True)
class _ServiceQuery(Query):
    slug: str = ""


def _contributor(command: type[Command], query: type[Query]) -> CqrsContributor:
    return CqrsContributor(
        pattern_name="wizard",
        command_types=(command,),
        query_types=(query,),
    )


def _install(runtime: MinimalRuntime, contributor: CqrsContributor | None) -> Registry[Any] | None:
    registries = runtime.registries
    registries.install("pattern", Registry("pattern"))
    registries.install("pattern_builder", Registry("pattern builder"))
    table: Registry[Any] | None = None
    if contributor is not None:
        table = Registry("cqrs contributor")
        registries.install("cqrs_contributor", table)
    register_wizard(registries)
    if table is not None and contributor is not None:
        installed = table.get("wizard")
        assert installed.command_types == wizard_cqrs_contributor().command_types
        assert installed.query_types == wizard_cqrs_contributor().query_types
        table.register("wizard", contributor)
    return table


def _start(runtime: MinimalRuntime) -> None:
    runtime.start(
        drivers=bind_memory(),
        structure_definition_id="local.embedded",
    )


def _stop(*runtimes: MinimalRuntime) -> None:
    for runtime in runtimes:
        if runtime.is_started:
            runtime.stop()


def _commands(
    runtime: MinimalRuntime,
    *,
    mode: CatalogMode = "standalone",
) -> tuple[type, ...]:
    return collect_cqrs_command_types(
        mode=mode,
        contributors=runtime.registries.require("cqrs_contributor"),
    )


def _queries(
    runtime: MinimalRuntime,
    *,
    mode: CatalogMode = "standalone",
) -> tuple[type, ...]:
    return collect_cqrs_query_types(
        mode=mode,
        contributors=runtime.registries.require("cqrs_contributor"),
    )


@pytest.fixture
def _process_contributors() -> Any:
    import palm.common.cqrs.service_contributors as service_registry
    import palm.common.patterns._registry as registry

    with registry._lock:
        saved_patterns = dict(registry._cqrs_contributors)
    with service_registry._lock:
        saved_services = dict(service_registry._contributors)
    register_cqrs_contributor(
        CqrsContributor(
            pattern_name="wizard",
            command_types=(_ProcessCommand,),
            query_types=(_ProcessQuery,),
        )
    )
    register_service_cqrs_contributor(
        ServiceCqrsContributor(
            service_name="_catalog_probe",
            command_types=(_ServiceCommand,),
            query_types=(_ServiceQuery,),
        )
    )
    try:
        yield
    finally:
        with registry._lock:
            registry._cqrs_contributors.clear()
            registry._cqrs_contributors.update(saved_patterns)
        with service_registry._lock:
            service_registry._contributors.clear()
            service_registry._contributors.update(saved_services)


def test_catalog_reads_the_system_registry(_process_contributors: None) -> None:
    del _process_contributors
    first = MinimalRuntime()
    second = MinimalRuntime()
    _install(first, _contributor(_CommandA, _QueryA))
    _install(second, _contributor(_CommandB, _QueryB))
    try:
        _start(first)
        _start(second)
        commands_a = _commands(first)
        commands_b = _commands(second)
        queries_a = _queries(first)
        queries_b = _queries(second)
        assert _CommandA in commands_a
        assert _CommandB in commands_b
        assert _CommandA not in commands_b
        assert _QueryA in queries_a
        assert _QueryB in queries_b
        assert _QueryA not in queries_b
        assert _ServiceCommand in commands_a
        assert _ServiceCommand in commands_b
        assert _ServiceQuery in queries_a
        assert _ServiceQuery in queries_b
        assert SubmitFlowCommand in commands_a
        assert _ProcessCommand not in commands_a
        assert _ProcessQuery not in queries_a
        host_queries = _queries(first, mode="host")
        assert _QueryA in host_queries
        assert GetResourceInvocationsQuery in host_queries
        assert GetResourceInvocationsQuery not in queries_a
        commands = CommandBus()
        query_bus = QueryBus()
        wire_standalone_buses(
            commands,
            query_bus,
            first,
            plan_registry=PlanRegistry(),
        )
        with pytest.raises(TypeError, match="Unsupported command: _CommandA"):
            commands.dispatch(_CommandA())
        with pytest.raises(TypeError, match="No handler registered for _ProcessCommand"):
            commands.dispatch(_ProcessCommand())
        with pytest.raises(TypeError, match="Unsupported query: _QueryA"):
            query_bus.ask(_QueryA())
        with pytest.raises(TypeError, match="No handler registered for _ProcessQuery"):
            query_bus.ask(_ProcessQuery())
        with pytest.raises(TypeError, match="No handler registered for GetResourceInvocationsQuery"):
            query_bus.ask(GetResourceInvocationsQuery())
        process = get_cqrs_contributor("wizard")
        assert process is not None
        assert process.command_types == (_ProcessCommand,)
    finally:
        _stop(first, second)


def test_catalog_ignores_the_process_table(_process_contributors: None) -> None:
    del _process_contributors
    runtime = MinimalRuntime()
    _install(runtime, None)
    try:
        _start(runtime)
        with pytest.raises(RuntimeError, match="cqrs_contributor"):
            wire_standalone_query_bus(QueryBus(), runtime)
        with pytest.raises(RuntimeError, match="cqrs_contributor"):
            _commands(runtime)
        process = get_cqrs_contributor("wizard")
        assert process is not None
        assert process.command_types == (_ProcessCommand,)
    finally:
        _stop(runtime)


def test_catalog_skips_a_missing_pattern_name(_process_contributors: None) -> None:
    del _process_contributors
    runtime = MinimalRuntime()
    table = _install(runtime, _contributor(_CommandA, _QueryA))
    assert table is not None
    table.drop("wizard")
    try:
        _start(runtime)
        commands = _commands(runtime)
        queries = _queries(runtime)
        assert _CommandA not in commands
        assert _ProcessCommand not in commands
        assert _ServiceCommand in commands
        assert SubmitFlowCommand in commands
        assert _QueryA not in queries
        assert _ProcessQuery not in queries
        assert _ServiceQuery in queries
        with pytest.raises(RegistryError, match="wizard"):
            table.get("wizard")
        process = get_cqrs_contributor("wizard")
        assert process is not None
        assert process.query_types == (_ProcessQuery,)
    finally:
        _stop(runtime)
