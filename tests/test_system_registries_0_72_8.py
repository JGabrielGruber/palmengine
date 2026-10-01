"""System instance owns its registries (0.72.8).

The set starts empty. The caller installs the tables a path reads.
``start`` freezes the set. Lookups do not consult the process-wide maps.
"""

from __future__ import annotations

from typing import Any

import pytest
from bundles.minimal.bind import bind_memory
from bundles.minimal.runtime import MinimalRuntime

from palm.common.exceptions import DefinitionBuildError
from palm.common.patterns.build_context import PatternBuildContext
from palm.common.patterns.builder import build_pattern
from palm.core.exceptions import RegistryError
from palm.core.registry import Registry, pattern_registry
from palm.core.resource.base_provider import BaseProvider
from palm.definitions.flow import FlowDefinition
from palm.system.bound import BoundDrivers, WorkloadRuntimeSlot
from palm.system.registries import SystemRegistries


class _Pattern:
    def __init__(self, name: str) -> None:
        self.name = name


class _Provider(BaseProvider):
    def connect(self) -> None:
        return None

    def fetch(self, resource_id: str, **params: Any) -> Any:
        return resource_id

    def disconnect(self) -> None:
        return None


def test_registry_set_starts_empty_and_install_is_once() -> None:
    registries = SystemRegistries()
    assert registries.names() == ()
    table = Registry("pattern")
    registries.install("pattern", table)
    assert registries.require("pattern") is table
    with pytest.raises(RuntimeError, match="already installed"):
        registries.install("pattern", Registry("pattern"))
    with pytest.raises(RuntimeError, match="no provider registry"):
        registries.require("provider")


def test_start_freezes_the_set_and_its_entries() -> None:
    runtime = MinimalRuntime()
    table = Registry("pattern")
    table.register("isolated", _Pattern)
    runtime.registries.install("pattern", table)
    runtime.start(drivers=bind_memory(), structure_definition_id="local.embedded")
    assert runtime.registries.frozen
    assert table.frozen
    with pytest.raises(RuntimeError, match="fixed"):
        runtime.registries.install("provider", Registry("provider"))
    with pytest.raises(RegistryError, match="fixed"):
        table.register("other", _Pattern)


def test_provider_lookup_reads_the_installed_registry() -> None:
    runtime = MinimalRuntime()
    with pytest.raises(RegistryError, match="no provider registry"):
        runtime.resource.use("echo")
    providers = Registry("provider")
    providers.register("echo", _Provider)
    runtime.registries.install("provider", providers)
    runtime.start(drivers=bind_memory(), structure_definition_id="local.embedded")
    assert isinstance(runtime.resource.use("echo"), _Provider)


def test_pattern_build_ignores_the_process_registry() -> None:
    pattern_registry.register("isolated-global", _Pattern)
    try:
        registries = SystemRegistries()
        flow = FlowDefinition(name="isolated", pattern="isolated-global")
        with pytest.raises(DefinitionBuildError, match="no system registries"):
            build_pattern(flow, context=PatternBuildContext())
        registries.install("pattern", Registry("pattern"))
        with pytest.raises(DefinitionBuildError, match="Cannot resolve pattern"):
            build_pattern(flow, context=PatternBuildContext(registries=registries))
        owned = Registry("pattern")
        owned.register("isolated-global", _Pattern)
        registries = SystemRegistries()
        registries.install("pattern", owned)
        pattern_registry.drop("isolated-global")
        built = build_pattern(flow, context=PatternBuildContext(registries=registries))
        assert isinstance(built, _Pattern)
    finally:
        pattern_registry.drop("isolated-global")


def test_named_workload_slot_requires_the_system_registry() -> None:
    runtime = MinimalRuntime()
    drivers = BoundDrivers(
        version=1,
        storage=bind_memory().storage,
        workload_runtime=WorkloadRuntimeSlot(names=("local",), default="local"),
    )
    with pytest.raises(RuntimeError, match="workload_runtime registry"):
        runtime.start(drivers=drivers, structure_definition_id="local.embedded")
