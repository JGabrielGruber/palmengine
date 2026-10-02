"""Instance inspect reads the system registry (0.72.15).

Inspect passes the ``cqrs_contributor`` table into the walk. A missing pattern
name is not read from the process list. A runtime that does not install the
table does not read that process list.
"""

from __future__ import annotations

from typing import Any

import pytest
from bundles.minimal.bind import bind_memory
from bundles.minimal.runtime import MinimalRuntime
from plugins.patterns.wizard.bindings.cqrs.handlers import handle_wizard_query
from plugins.patterns.wizard.bindings.cqrs.queries import GetWizardStatusQuery
from plugins.patterns.wizard.registry import register as register_wizard

from palm.common.cqrs.instance_inspect import handle_inspect_instance
from palm.common.cqrs.query import InspectInstanceQuery
from palm.common.cqrs.standalone import StandaloneQueryHandlers
from palm.common.patterns._registry import (
    CqrsContributor,
    get_cqrs_contributor,
    register_cqrs_contributor,
)
from palm.core.exceptions import RegistryError
from palm.core.registry import Registry


def _contributor(tag: str) -> CqrsContributor:
    def handle_query(query: Any, ctx: Any) -> dict[str, Any]:
        del ctx
        return {"tag": tag, "instance_id": query.instance_id}

    return CqrsContributor(
        pattern_name="wizard",
        instance_status_query=GetWizardStatusQuery,
        handle_query=handle_query,
    )


_PROCESS_CALLS = {"n": 0}


def _process_query(query: Any, ctx: Any) -> dict[str, Any]:
    del ctx
    _PROCESS_CALLS["n"] += 1
    return {"tag": "P", "instance_id": query.instance_id}


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
        assert installed.handle_query is handle_wizard_query
        assert installed.instance_status_query is GetWizardStatusQuery
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


def _inspect(runtime: MinimalRuntime, instance_id: str) -> Any:
    return StandaloneQueryHandlers(runtime).ask(InspectInstanceQuery(instance_id=instance_id))


@pytest.fixture
def _process_contributors() -> Any:
    import palm.common.patterns._registry as registry

    _PROCESS_CALLS["n"] = 0
    with registry._lock:
        saved = dict(registry._cqrs_contributors)
    register_cqrs_contributor(
        CqrsContributor(
            pattern_name="wizard",
            query_types=(GetWizardStatusQuery,),
            instance_status_query=GetWizardStatusQuery,
            handle_query=_process_query,
        )
    )
    try:
        yield
    finally:
        _PROCESS_CALLS["n"] = 0
        with registry._lock:
            registry._cqrs_contributors.clear()
            registry._cqrs_contributors.update(saved)


def test_instance_inspect_reads_the_system_registry(_process_contributors: None) -> None:
    del _process_contributors
    first = MinimalRuntime()
    second = MinimalRuntime()
    _install(first, _contributor("A"))
    _install(second, _contributor("B"))
    try:
        _start(first)
        _start(second)
        assert _inspect(first, "inst-a") == {"tag": "A", "instance_id": "inst-a"}
        assert _inspect(second, "inst-b") == {"tag": "B", "instance_id": "inst-b"}
        process = get_cqrs_contributor("wizard")
        assert process is not None
        assert process.handle_query is _process_query
        assert _PROCESS_CALLS["n"] == 0
    finally:
        _stop(first, second)


def test_instance_inspect_ignores_the_process_table(_process_contributors: None) -> None:
    del _process_contributors
    runtime = MinimalRuntime()
    _install(runtime, None)
    try:
        _start(runtime)
        with pytest.raises(RuntimeError, match="cqrs_contributor"):
            _inspect(runtime, "inst-a")
        process = get_cqrs_contributor("wizard")
        assert process is not None
        assert process.handle_query is _process_query
        assert _PROCESS_CALLS["n"] == 0
    finally:
        _stop(runtime)


def test_instance_inspect_skips_a_missing_pattern_name(_process_contributors: None) -> None:
    del _process_contributors
    runtime = MinimalRuntime()
    table = _install(runtime, _contributor("A"))
    assert table is not None
    table.drop("wizard")
    try:
        _start(runtime)
        assert _inspect(runtime, "inst-a") is None
        assert (
            handle_inspect_instance(
                InspectInstanceQuery(instance_id="inst-a"),
                object(),
                contributors=runtime.registries.require("cqrs_contributor"),
            )
            is None
        )
        with pytest.raises(RegistryError, match="wizard"):
            table.get("wizard")
        process = get_cqrs_contributor("wizard")
        assert process is not None
        assert process.handle_query is _process_query
        assert _PROCESS_CALLS["n"] == 0
    finally:
        _stop(runtime)
