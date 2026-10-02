"""Schema build reads the system registry (0.72.16).

``build_schema_registry`` copies pattern schemas from the ``cqrs_contributor``
table the caller passes. A missing pattern name is not copied from the process
list. A runtime that does not install the table does not read that list.
Service schemas stay on the process service list.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import pytest
from bundles.minimal.bind import bind_memory
from bundles.minimal.runtime import MinimalRuntime
from bundles.standard.runtimes.server.surfaces.rest.schemas import named_schemas
from plugins.patterns.wizard.bindings.cqrs.commands import (
    ProvideWizardInputCommand,
    RequestWizardBacktrackCommand,
)
from plugins.patterns.wizard.bindings.cqrs.contributor import wizard_cqrs_contributor
from plugins.patterns.wizard.registry import register as register_wizard

from palm.common.cqrs.command import Command
from palm.common.cqrs.schemas import build_schema_registry
from palm.common.cqrs.service_contributors import (
    ServiceCqrsContributor,
    register_service_cqrs_contributor,
)
from palm.common.patterns._registry import (
    CqrsContributor,
    get_cqrs_contributor,
    register_cqrs_contributor,
)
from palm.core.context.state_schema import DictStateSchema
from palm.core.exceptions import RegistryError
from palm.core.registry import Registry


@dataclass(frozen=True)
class _ServiceCommand(Command):
    slug: str


def _marked(tag: str) -> DictStateSchema:
    return DictStateSchema(
        {
            "type": "object",
            "properties": {"value": {"type": "string", "description": tag}},
            "required": ["value"],
        }
    )


_PROCESS_SCHEMA = _marked("P")
_BACKTRACK = DictStateSchema(
    {
        "type": "object",
        "properties": {"to_step": {"type": "string"}},
    }
)
_SERVICE_SCHEMA = DictStateSchema(
    {
        "type": "object",
        "properties": {"slug": {"type": "string"}},
        "required": ["slug"],
    }
)


def _contributor(schema: DictStateSchema) -> CqrsContributor:
    return CqrsContributor(
        pattern_name="wizard",
        command_schemas={
            ProvideWizardInputCommand: schema,
            RequestWizardBacktrackCommand: _BACKTRACK,
        },
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
        assert installed.command_schemas is wizard_cqrs_contributor().command_schemas
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


def _build(runtime: MinimalRuntime) -> Any:
    return build_schema_registry(
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
            command_schemas={
                ProvideWizardInputCommand: _PROCESS_SCHEMA,
                RequestWizardBacktrackCommand: _BACKTRACK,
            },
        )
    )
    register_service_cqrs_contributor(
        ServiceCqrsContributor(
            service_name="_schema_probe",
            command_types=(_ServiceCommand,),
            command_schemas={_ServiceCommand: _SERVICE_SCHEMA},
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


def test_schema_build_reads_the_system_registry(_process_contributors: None) -> None:
    del _process_contributors
    schema_a = _marked("A")
    schema_b = _marked("B")
    first = MinimalRuntime()
    second = MinimalRuntime()
    _install(first, _contributor(schema_a))
    _install(second, _contributor(schema_b))
    try:
        _start(first)
        _start(second)
        built_a = _build(first)
        built_b = _build(second)
        assert built_a.schema_for(ProvideWizardInputCommand) is schema_a
        assert built_b.schema_for(ProvideWizardInputCommand) is schema_b
        assert built_a.schema_for(_ServiceCommand) is _SERVICE_SCHEMA
        assert built_b.schema_for(_ServiceCommand) is _SERVICE_SCHEMA
        bodies_a = named_schemas(contributors=first.registries.require("cqrs_contributor"))
        bodies_b = named_schemas(contributors=second.registries.require("cqrs_contributor"))
        assert bodies_a["WizardInputBody"].definition["properties"]["value"]["description"] == "A"
        assert bodies_b["WizardInputBody"].definition["properties"]["value"]["description"] == "B"
        process = get_cqrs_contributor("wizard")
        assert process is not None
        assert process.command_schemas[ProvideWizardInputCommand] is _PROCESS_SCHEMA
    finally:
        _stop(first, second)


def test_schema_build_ignores_the_process_table(_process_contributors: None) -> None:
    del _process_contributors
    runtime = MinimalRuntime()
    _install(runtime, None)
    try:
        _start(runtime)
        with pytest.raises(RuntimeError, match="cqrs_contributor"):
            _build(runtime)
        process = get_cqrs_contributor("wizard")
        assert process is not None
        assert process.command_schemas[ProvideWizardInputCommand] is _PROCESS_SCHEMA
    finally:
        _stop(runtime)


def test_schema_build_skips_a_missing_pattern_name(_process_contributors: None) -> None:
    del _process_contributors
    runtime = MinimalRuntime()
    table = _install(runtime, _contributor(_marked("A")))
    assert table is not None
    table.drop("wizard")
    try:
        _start(runtime)
        built = _build(runtime)
        assert built.schema_for(ProvideWizardInputCommand) is None
        assert built.schema_for(_ServiceCommand) is _SERVICE_SCHEMA
        with pytest.raises(KeyError, match="ProvideWizardInputCommand"):
            named_schemas(contributors=runtime.registries.require("cqrs_contributor"))
        with pytest.raises(RegistryError, match="wizard"):
            table.get("wizard")
        process = get_cqrs_contributor("wizard")
        assert process is not None
        assert process.command_schemas[ProvideWizardInputCommand] is _PROCESS_SCHEMA
    finally:
        _stop(runtime)
