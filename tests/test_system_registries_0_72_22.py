"""Session enrichment reads the system registry (0.72.22).

``enrich_session_view`` reads the ``session_enricher`` table the caller
passes. A missing pattern name is not read from the process map. A runtime
that does not install the table does not read that map.
"""

from __future__ import annotations

from typing import Any

import pytest
from bundles.minimal.bind import bind_memory
from bundles.minimal.runtime import MinimalRuntime
from services.execution.flows.service import FlowExecutionService
from services.execution.flows.session import FlowSession

from palm.common.patterns._registry import (
    enrich_session_view,
    get_session_enricher,
    register_session_enricher,
)
from palm.core.exceptions import RegistryError
from palm.core.registry import Registry

_VIEW = {"status": "RUNNING", "metadata": {"pattern": "wizard"}, "prompt": "Name?"}
_PROCESS_CALLS = {"n": 0}


def _process(view: dict[str, Any]) -> dict[str, str]:
    del view
    _PROCESS_CALLS["n"] += 1
    return {"tag": "P"}


def _enrich(tag: str):
    def enrich(view: dict[str, Any]) -> dict[str, Any]:
        return {"tag": tag, "prompt": view.get("prompt")}

    return enrich


class _Inspect:
    def __init__(self, view: dict[str, Any]) -> None:
        self._view = view

    def inspect_instance(self, session_id: str) -> dict[str, Any]:
        del session_id
        return dict(self._view)


class _Flows:
    def __init__(self, runtime: MinimalRuntime, view: dict[str, Any]) -> None:
        self._runtime = runtime
        self._view = view

    def resolve_runtime(self, name: str | None = None) -> MinimalRuntime:
        del name
        return self._runtime

    def inspect_session(self, session_id: str) -> dict[str, Any]:
        del session_id
        return dict(self._view)

    def get_instance_metadata(self, session_id: str) -> dict[str, Any]:
        del session_id
        return {}


def _install(runtime: MinimalRuntime, enricher: Any | None) -> Registry[Any] | None:
    registries = runtime.registries
    registries.install("pattern", Registry("pattern"))
    registries.install("pattern_builder", Registry("pattern builder"))
    table: Registry[Any] | None = None
    if enricher is not None:
        table = Registry("session enricher")
        registries.install("session_enricher", table)
        table.register("wizard", enricher)
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


def _service(runtime: MinimalRuntime, view: dict[str, Any]) -> FlowExecutionService:
    return FlowExecutionService(
        commands=object(),
        queries=object(),
        schemas=object(),
        inspect=_Inspect(view),
        runtime=runtime,
    )


def _session(runtime: MinimalRuntime, view: dict[str, Any]) -> FlowSession:
    return FlowSession(_Flows(runtime, view), flow_id="flow", session_id="inst")


@pytest.fixture
def _process_enrichers() -> Any:
    import palm.common.patterns._registry as registry

    _PROCESS_CALLS["n"] = 0
    with registry._lock:
        saved = dict(registry._session_enrichers)
    register_session_enricher("wizard", _process)
    try:
        yield
    finally:
        _PROCESS_CALLS["n"] = 0
        with registry._lock:
            registry._session_enrichers.clear()
            registry._session_enrichers.update(saved)


def test_session_enrichment_reads_the_system_registry(_process_enrichers: None) -> None:
    del _process_enrichers
    first = MinimalRuntime()
    second = MinimalRuntime()
    _install(first, _enrich("A"))
    _install(second, _enrich("B"))
    try:
        _start(first)
        _start(second)
        first_table = first.registries.require("session_enricher")
        enriched = enrich_session_view("wizard", _VIEW, enrichers=first_table)
        assert enriched["tag"] == "A"
        service_ctx = _service(first, _VIEW).session_context(flow_id="flow", session_id="inst")
        assert service_ctx.detail["tag"] == "A"
        assert _session(second, _VIEW).context().detail["tag"] == "B"
        assert enrich_session_view(None, _VIEW, enrichers=first_table) == {}
        assert _PROCESS_CALLS["n"] == 0
        assert get_session_enricher("wizard") is _process
    finally:
        _stop(first, second)


def test_session_enrichment_ignores_the_process_table(_process_enrichers: None) -> None:
    del _process_enrichers
    runtime = MinimalRuntime()
    _install(runtime, None)
    try:
        _start(runtime)
        with pytest.raises(RuntimeError, match="session_enricher"):
            _service(runtime, _VIEW).session_context(flow_id="flow", session_id="inst")
        with pytest.raises(RuntimeError, match="session_enricher"):
            _session(runtime, _VIEW).context()
        assert _PROCESS_CALLS["n"] == 0
        assert get_session_enricher("wizard") is _process
    finally:
        _stop(runtime)


def test_session_enrichment_raises_for_a_missing_pattern_name(_process_enrichers: None) -> None:
    del _process_enrichers
    runtime = MinimalRuntime()
    table = _install(runtime, _enrich("A"))
    assert table is not None
    table.drop("wizard")
    try:
        _start(runtime)
        with pytest.raises(RegistryError, match="wizard"):
            enrich_session_view(
                "wizard",
                _VIEW,
                enrichers=runtime.registries.require("session_enricher"),
            )
        with pytest.raises(RegistryError, match="wizard"):
            _session(runtime, _VIEW).context()
        assert _PROCESS_CALLS["n"] == 0
        assert get_session_enricher("wizard") is _process
    finally:
        _stop(runtime)
