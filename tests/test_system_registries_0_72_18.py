"""Standalone command dispatch reads the system registry (0.72.18).

``StandaloneCommandHandlers.handle`` scans the ``cqrs_contributor`` table the
caller passes. A missing pattern name is not read from the process list. A
runtime that does not install the table does not read that list.
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
from palm.common.cqrs.command import Command
from palm.common.cqrs.standalone import StandaloneCommandHandlers, wire_standalone_buses
from palm.common.patterns._registry import (
    CqrsContributor,
    get_cqrs_contributor,
    register_cqrs_contributor,
)
from palm.common.plans.registry import PlanRegistry
from palm.core.exceptions import RegistryError
from palm.core.registry import Registry


@dataclass(frozen=True)
class _Mark(Command):
    pass


_PROCESS_CALLS = {"n": 0}


def _process_handle(command: Command, ctx: Any) -> str:
    del command, ctx
    _PROCESS_CALLS["n"] += 1
    return "P"


def _contributor(tag: str) -> CqrsContributor:
    def handle_command(command: Command, ctx: Any) -> str:
        del command, ctx
        return tag

    return CqrsContributor(
        pattern_name="wizard",
        command_types=(_Mark,),
        handle_command=handle_command,
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
        assert installed.handle_command is wizard_cqrs_contributor().handle_command
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


def _handler(runtime: MinimalRuntime) -> StandaloneCommandHandlers:
    return StandaloneCommandHandlers(
        runtime,
        plan_registry=PlanRegistry(),
        contributors=runtime.registries.require("cqrs_contributor"),
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
            command_types=(_Mark,),
            handle_command=_process_handle,
        )
    )
    try:
        yield
    finally:
        _PROCESS_CALLS["n"] = 0
        with registry._lock:
            registry._cqrs_contributors.clear()
            registry._cqrs_contributors.update(saved)


def test_command_dispatch_reads_the_system_registry(_process_contributors: None) -> None:
    del _process_contributors
    first = MinimalRuntime()
    second = MinimalRuntime()
    _install(first, _contributor("A"))
    _install(second, _contributor("B"))
    try:
        _start(first)
        _start(second)
        assert _handler(first).handle(_Mark()) == "A"
        assert _handler(second).handle(_Mark()) == "B"
        bus = CommandBus()
        wire_standalone_buses(
            bus,
            QueryBus(),
            first,
            plan_registry=PlanRegistry(),
        )
        assert bus.dispatch(_Mark()) == "A"
        assert _PROCESS_CALLS["n"] == 0
        process = get_cqrs_contributor("wizard")
        assert process is not None
        assert process.handle_command is _process_handle
    finally:
        _stop(first, second)


def test_command_dispatch_ignores_the_process_table(_process_contributors: None) -> None:
    del _process_contributors
    runtime = MinimalRuntime()
    _install(runtime, None)
    try:
        _start(runtime)
        with pytest.raises(RuntimeError, match="cqrs_contributor"):
            wire_standalone_buses(
                CommandBus(),
                QueryBus(),
                runtime,
                plan_registry=PlanRegistry(),
            )
        with pytest.raises(RuntimeError, match="cqrs_contributor"):
            _handler(runtime)
        assert _PROCESS_CALLS["n"] == 0
        process = get_cqrs_contributor("wizard")
        assert process is not None
        assert process.handle_command is _process_handle
    finally:
        _stop(runtime)


def test_command_dispatch_skips_a_missing_pattern_name(_process_contributors: None) -> None:
    del _process_contributors
    runtime = MinimalRuntime()
    table = _install(runtime, _contributor("A"))
    assert table is not None
    table.drop("wizard")
    try:
        _start(runtime)
        with pytest.raises(TypeError, match="Unsupported command: _Mark"):
            _handler(runtime).handle(_Mark())
        with pytest.raises(RegistryError, match="wizard"):
            table.get("wizard")
        assert _PROCESS_CALLS["n"] == 0
        process = get_cqrs_contributor("wizard")
        assert process is not None
        assert process.handle_command is _process_handle
    finally:
        _stop(runtime)
