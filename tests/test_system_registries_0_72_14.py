"""Wizard status reads the system registry (0.72.14).

The status query passes the ``read_model_builder`` table into
``build_pattern_read_model``. A missing pattern name raises. The process
read-model table is not a fallback. A runtime that does not install the table
does not read that process table.
"""

from __future__ import annotations

from typing import Any

import pytest
from bundles.minimal.bind import bind_memory
from bundles.minimal.runtime import MinimalRuntime
from plugins.patterns.wizard.bindings.cqrs.handlers import get_wizard_status
from plugins.patterns.wizard.bindings.cqrs.queries import GetWizardStatusQuery
from plugins.patterns.wizard.bindings.read_model import build_wizard_view
from plugins.patterns.wizard.registry import register as register_wizard

from palm.common.patterns._registry import (
    get_read_model_builder,
    register_read_model_builder,
)
from palm.common.patterns.pattern_read_model import build_pattern_read_model
from palm.core.exceptions import RegistryError
from palm.core.registry import Registry


def _builder(tag: str) -> Any:
    def build(instance: dict[str, Any], **kwargs: Any) -> dict[str, Any]:
        del kwargs
        return {"tag": tag, "instance_id": instance["instance_id"]}

    return build


def _process_builder(instance: dict[str, Any], **kwargs: Any) -> dict[str, Any]:
    del instance, kwargs
    return {"tag": "P"}


def _install(runtime: MinimalRuntime, builder: Any | None) -> Registry[Any] | None:
    registries = runtime.registries
    registries.install("pattern", Registry("pattern"))
    registries.install("pattern_builder", Registry("pattern builder"))
    table: Registry[Any] | None = None
    if builder is not None:
        table = Registry("read-model builder")
        registries.install("read_model_builder", table)
    register_wizard(registries)
    if table is not None and builder is not None:
        assert table.get("wizard") is build_wizard_view
        table.register("wizard", builder)
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


class _StatusCtx:
    def __init__(self, runtime: MinimalRuntime) -> None:
        self._runtime = runtime
        self._pattern_projections: dict[str, Any] = {}

    def _get_instance(self, query: GetWizardStatusQuery) -> dict[str, Any]:
        return {"instance_id": query.instance_id, "job_id": "job-1"}


def _status(runtime: MinimalRuntime, instance_id: str) -> dict[str, Any] | None:
    return get_wizard_status(GetWizardStatusQuery(instance_id=instance_id), _StatusCtx(runtime))


@pytest.fixture
def _process_read_model() -> Any:
    import palm.common.patterns._registry as registry

    with registry._lock:
        saved = dict(registry._read_model_builders)
    register_read_model_builder("wizard", _process_builder)
    try:
        yield
    finally:
        with registry._lock:
            registry._read_model_builders.clear()
            registry._read_model_builders.update(saved)


def test_wizard_status_reads_the_system_registry(_process_read_model: None) -> None:
    del _process_read_model
    first = MinimalRuntime()
    second = MinimalRuntime()
    _install(first, _builder("A"))
    _install(second, _builder("B"))
    try:
        _start(first)
        _start(second)
        assert _status(first, "inst-a") == {"tag": "A", "instance_id": "inst-a"}
        assert _status(second, "inst-b") == {"tag": "B", "instance_id": "inst-b"}
        process = get_read_model_builder("wizard")
        assert process is not None
        assert process({}) == {"tag": "P"}
    finally:
        _stop(first, second)


def test_read_model_builder_ignores_the_process_table(_process_read_model: None) -> None:
    del _process_read_model
    runtime = MinimalRuntime()
    _install(runtime, None)
    try:
        _start(runtime)
        with pytest.raises(RuntimeError, match="read_model_builder"):
            _status(runtime, "inst-missing-table")
        process = get_read_model_builder("wizard")
        assert process is not None
        assert process({}) == {"tag": "P"}
    finally:
        _stop(runtime)


def test_read_model_builder_requires_the_pattern_name(_process_read_model: None) -> None:
    del _process_read_model
    runtime = MinimalRuntime()
    table = _install(runtime, _builder("A"))
    assert table is not None
    table.drop("wizard")
    try:
        _start(runtime)
        with pytest.raises(RegistryError, match="wizard"):
            _status(runtime, "inst-missing-name")
        with pytest.raises(RegistryError, match="wizard"):
            build_pattern_read_model(
                "wizard",
                {"instance_id": "inst-missing-name"},
                builders=runtime.registries.require("read_model_builder"),
            )
        process = get_read_model_builder("wizard")
        assert process is not None
        assert process({}) == {"tag": "P"}
    finally:
        _stop(runtime)
