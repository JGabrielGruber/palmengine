"""Standard host query dispatch reads the system registry (0.72.21).

``HostQueryHandlers.ask`` scans the ``cqrs_contributor`` table the caller
passes. A missing pattern name is not read from the process list. A runtime
that does not install the table does not read that list.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import pytest
from bundles.minimal.bind import bind_memory
from bundles.minimal.runtime import MinimalRuntime
from bundles.standard.app.host.wiring.cqrs import HostQueryHandlers, wire_query_bus
from plugins.patterns.wizard.bindings.cqrs.contributor import wizard_cqrs_contributor
from plugins.patterns.wizard.registry import register as register_wizard

from palm.common.cqrs.bus import QueryBus
from palm.common.cqrs.query import Query
from palm.common.patterns._registry import (
    CqrsContributor,
    get_cqrs_contributor,
    register_cqrs_contributor,
)
from palm.core.exceptions import RegistryError
from palm.core.registry import Registry


@dataclass(frozen=True)
class _Mark(Query):
    pass


_PROCESS_CALLS = {"n": 0}


def _process_handle(query: Query, ctx: Any) -> str:
    del query, ctx
    _PROCESS_CALLS["n"] += 1
    return "P"


def _contributor(tag: str) -> CqrsContributor:
    def handle_query(query: Query, ctx: Any) -> str:
        del query, ctx
        return tag

    return CqrsContributor(
        pattern_name="wizard",
        query_types=(_Mark,),
        handle_query=handle_query,
    )


class _Host:
    def __init__(self, runtime: MinimalRuntime) -> None:
        self._runtime = runtime

    def runtime(self, name: str | None = None) -> MinimalRuntime:
        del name
        return self._runtime


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
        assert installed.handle_query is wizard_cqrs_contributor().handle_query
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


def _handler(runtime: MinimalRuntime) -> HostQueryHandlers:
    return HostQueryHandlers(
        app=_Host(runtime),
        instances=object(),
        pattern_projections={},
        resource_invocations=object(),
        job_board=object(),
        instance_manager=object(),
        contributors=runtime.registries.require("cqrs_contributor"),
    )


def _wire(bus: QueryBus, runtime: MinimalRuntime) -> None:
    wire_query_bus(
        bus,
        app=_Host(runtime),
        instances=object(),
        pattern_projections={},
        resource_invocations=object(),
        job_board=object(),
        instance_manager=object(),
    )


@pytest.fixture
def _process_contributors() -> Any:
    import palm.common.patterns._registry as registry

    _PROCESS_CALLS["n"] = 0
    with registry._lock:
        saved = dict(registry._cqrs_contributors)
    register_cqrs_contributor(
        CqrsContributor(
            pattern_name="wizard",
            query_types=(_Mark,),
            handle_query=_process_handle,
        )
    )
    try:
        yield
    finally:
        _PROCESS_CALLS["n"] = 0
        with registry._lock:
            registry._cqrs_contributors.clear()
            registry._cqrs_contributors.update(saved)


def test_host_query_dispatch_reads_the_system_registry(_process_contributors: None) -> None:
    del _process_contributors
    first = MinimalRuntime()
    second = MinimalRuntime()
    _install(first, _contributor("A"))
    _install(second, _contributor("B"))
    try:
        _start(first)
        _start(second)
        assert _handler(first).ask(_Mark()) == "A"
        assert _handler(second).ask(_Mark()) == "B"
        bus = QueryBus()
        _wire(bus, first)
        assert bus.ask(_Mark()) == "A"
        assert _PROCESS_CALLS["n"] == 0
        process = get_cqrs_contributor("wizard")
        assert process is not None
        assert process.handle_query is _process_handle
    finally:
        _stop(first, second)


def test_host_query_dispatch_ignores_the_process_table(_process_contributors: None) -> None:
    del _process_contributors
    runtime = MinimalRuntime()
    _install(runtime, None)
    try:
        _start(runtime)
        with pytest.raises(RuntimeError, match="cqrs_contributor"):
            _wire(QueryBus(), runtime)
        with pytest.raises(RuntimeError, match="cqrs_contributor"):
            _handler(runtime)
        assert _PROCESS_CALLS["n"] == 0
        process = get_cqrs_contributor("wizard")
        assert process is not None
        assert process.handle_query is _process_handle
    finally:
        _stop(runtime)


def test_host_query_dispatch_skips_a_missing_pattern_name(_process_contributors: None) -> None:
    del _process_contributors
    runtime = MinimalRuntime()
    table = _install(runtime, _contributor("A"))
    assert table is not None
    table.drop("wizard")
    try:
        _start(runtime)
        with pytest.raises(TypeError, match="Unsupported query: _Mark"):
            _handler(runtime).ask(_Mark())
        with pytest.raises(RegistryError, match="wizard"):
            table.get("wizard")
        assert _PROCESS_CALLS["n"] == 0
        process = get_cqrs_contributor("wizard")
        assert process is not None
        assert process.handle_query is _process_handle
    finally:
        _stop(runtime)
