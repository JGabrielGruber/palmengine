"""Design contributor wiring reads the system registries (0.72.23).

``wire_builtin_design_contributors`` reads ``design_contributor_hook`` and
``provider_design_contributor_hook`` from the caller. A missing name is not
read from the process hook maps. A runtime that does not install a table
does not read those maps.
"""

from __future__ import annotations

from typing import Any

import pytest
from bundles.minimal.bind import bind_memory
from bundles.minimal.runtime import MinimalRuntime
from bundles.standard.app.host.services.packaging import apply_product_packaging
from services.design.registry import clear_design_contributors, iter_design_contributors

from palm.common.cqrs.bus import CommandBus, QueryBus
from palm.common.patterns._registry import (
    DesignContributorHook,
    get_design_contributor_hook,
    register_design_contributor_hook,
)
from palm.common.providers._registry import (
    iter_provider_design_contributor_hooks,
    register_provider_design_contributor_hook,
)
from palm.core.exceptions import RegistryError
from palm.core.registry import Registry

_PROCESS = {"pattern": 0, "provider": 0}


def _process_pattern() -> None:
    _PROCESS["pattern"] += 1


def _process_provider() -> None:
    _PROCESS["provider"] += 1


def _pattern(calls: list[str], tag: str) -> DesignContributorHook:
    def register() -> None:
        calls.append(f"pattern:{tag}")

    return DesignContributorHook(pattern_name="wizard", register=register)


def _provider(calls: list[str], tag: str):
    def hook() -> None:
        calls.append(f"provider:{tag}")

    return hook


def _base(runtime: MinimalRuntime) -> None:
    registries = runtime.registries
    registries.install("pattern", Registry("pattern"))
    registries.install("pattern_builder", Registry("pattern builder"))


def _install_hooks(
    runtime: MinimalRuntime,
    pattern: DesignContributorHook | None,
    provider: Any | None,
) -> None:
    _base(runtime)
    registries = runtime.registries
    if pattern is not None:
        table = Registry("design contributor hook")
        table.register("wizard", pattern)
        registries.install("design_contributor_hook", table)
    if provider is not None:
        table = Registry("provider design contributor hook")
        table.register("file", provider)
        registries.install("provider_design_contributor_hook", table)


def _install_empty(runtime: MinimalRuntime) -> None:
    _base(runtime)
    registries = runtime.registries
    registries.install("design_contributor_hook", Registry("design contributor hook"))
    registries.install(
        "provider_design_contributor_hook",
        Registry("provider design contributor hook"),
    )


def _start(runtime: MinimalRuntime) -> None:
    runtime.start(
        drivers=bind_memory(),
        structure_definition_id="local.embedded",
    )


def _stop(*runtimes: MinimalRuntime) -> None:
    for runtime in runtimes:
        if runtime.is_started:
            runtime.stop()


def _package(runtime: MinimalRuntime) -> None:
    apply_product_packaging(
        {"design": object(), "execution": None},
        command_bus=CommandBus(),
        query_bus=QueryBus(),
        repository=object(),
        instance_manager=object(),
        registries=runtime.registries,
    )


@pytest.fixture
def _process_hooks() -> Any:
    import services.design.registry as design_registry

    import palm.common.patterns._registry as pattern_registry
    import palm.common.providers._registry as provider_registry

    _PROCESS["pattern"] = 0
    _PROCESS["provider"] = 0
    with pattern_registry._lock:
        saved_patterns = dict(pattern_registry._design_contributor_hooks)
    with provider_registry._lock:
        saved_providers = list(provider_registry._design_contributor_hooks)
    with design_registry._lock:
        saved_design = dict(design_registry._contributors)
    register_design_contributor_hook(
        DesignContributorHook(pattern_name="wizard", register=_process_pattern)
    )
    register_provider_design_contributor_hook(_process_provider)
    try:
        yield
    finally:
        _PROCESS["pattern"] = 0
        _PROCESS["provider"] = 0
        with pattern_registry._lock:
            pattern_registry._design_contributor_hooks.clear()
            pattern_registry._design_contributor_hooks.update(saved_patterns)
        with provider_registry._lock:
            provider_registry._design_contributor_hooks.clear()
            provider_registry._design_contributor_hooks.extend(saved_providers)
        with design_registry._lock:
            design_registry._contributors.clear()
            design_registry._contributors.update(saved_design)


def _contributor_ids() -> set[str]:
    return {row.contributor_id for row in iter_design_contributors()}


def test_design_wiring_reads_the_system_registries(_process_hooks: None) -> None:
    del _process_hooks
    calls: list[str] = []
    first = MinimalRuntime()
    second = MinimalRuntime()
    _install_hooks(first, _pattern(calls, "A"), _provider(calls, "A"))
    _install_hooks(second, _pattern(calls, "B"), _provider(calls, "B"))
    try:
        _start(first)
        _start(second)
        clear_design_contributors()
        _package(first)
        _package(second)
        assert calls == ["pattern:A", "provider:A", "pattern:B", "provider:B"]
        assert _contributor_ids() == {"dashboard"}
        assert _PROCESS == {"pattern": 0, "provider": 0}
        assert get_design_contributor_hook("wizard").register is _process_pattern
        assert _process_provider in iter_provider_design_contributor_hooks()
    finally:
        _stop(first, second)


def test_design_wiring_ignores_the_process_maps(_process_hooks: None) -> None:
    del _process_hooks
    runtime = MinimalRuntime()
    _install_empty(runtime)
    try:
        _start(runtime)
        clear_design_contributors()
        _package(runtime)
        assert _contributor_ids() == {"dashboard"}
        assert _PROCESS == {"pattern": 0, "provider": 0}
        assert get_design_contributor_hook("wizard").register is _process_pattern
        assert _process_provider in iter_provider_design_contributor_hooks()
    finally:
        _stop(runtime)


def test_design_wiring_requires_both_tables(_process_hooks: None) -> None:
    del _process_hooks
    calls: list[str] = []
    bare = MinimalRuntime()
    pattern_only = MinimalRuntime()
    _base(bare)
    _install_hooks(pattern_only, _pattern(calls, "A"), None)
    try:
        _start(bare)
        _start(pattern_only)
        with pytest.raises(RuntimeError, match="no design_contributor_hook registry"):
            _package(bare)
        with pytest.raises(RuntimeError, match="no provider_design_contributor_hook registry"):
            _package(pattern_only)
        assert calls == []
        assert _PROCESS == {"pattern": 0, "provider": 0}
        assert get_design_contributor_hook("wizard").register is _process_pattern
        assert _process_provider in iter_provider_design_contributor_hooks()
    finally:
        _stop(bare, pattern_only)


def test_design_wiring_skips_a_missing_name(_process_hooks: None) -> None:
    del _process_hooks
    calls: list[str] = []
    dropped_pattern = MinimalRuntime()
    dropped_provider = MinimalRuntime()
    _install_hooks(dropped_pattern, _pattern(calls, "A"), _provider(calls, "A"))
    _install_hooks(dropped_provider, _pattern(calls, "B"), _provider(calls, "B"))
    dropped_pattern.registries.require("design_contributor_hook").drop("wizard")
    dropped_provider.registries.require("provider_design_contributor_hook").drop("file")
    try:
        _start(dropped_pattern)
        _start(dropped_provider)
        clear_design_contributors()
        _package(dropped_pattern)
        assert calls == ["provider:A"]
        with pytest.raises(RegistryError, match="wizard"):
            dropped_pattern.registries.require("design_contributor_hook").get("wizard")
        calls.clear()
        _package(dropped_provider)
        assert calls == ["pattern:B"]
        with pytest.raises(RegistryError, match="file"):
            dropped_provider.registries.require("provider_design_contributor_hook").get("file")
        assert _PROCESS == {"pattern": 0, "provider": 0}
        assert get_design_contributor_hook("wizard").register is _process_pattern
        assert _process_provider in iter_provider_design_contributor_hooks()
    finally:
        _stop(dropped_pattern, dropped_provider)
