"""Todo-path reads use the system instance (0.72.9).

``system.bind`` and ``stop`` read registries on the runtime.
Kv uses that runtime's storage. Wizard build reads ``wizard_step`` there.
A missing name raises. Process-wide hooks are not a fallback.
"""

from __future__ import annotations

import pytest
from bundles.minimal.bind import bind_memory
from bundles.minimal.runtime import MinimalRuntime
from plugins.patterns.wizard.flow.extensions.registry import (
    default_wizard_step_registry,
    register_builtin_wizard_step_kinds,
)
from plugins.patterns.wizard.registry import register as register_wizard
from plugins.providers.kv.provider import KvProvider

from palm.common.patterns.build_context import PatternBuildContext
from palm.common.patterns.builder import build_pattern
from palm.common.providers._registry import (
    clear_runtime_binding,
    register_runtime_accessor,
    register_runtime_binding,
)
from palm.common.resource.document_storage import (
    build_memory_key,
    build_storage_key,
    get_memory_kv_store,
)
from palm.core.registry import Registry
from palm.definitions.flow import FlowDefinition


def _flow(*, include_commit: bool = False) -> FlowDefinition:
    options: dict[str, object] = {
        "include_commit": include_commit,
        "steps": [
            {
                "slug": "save",
                "title": "Save",
                "prompt": "save",
                "step_kind": "resource",
                "resource_ref": "put-palm-todos",
            },
        ],
    }
    if include_commit:
        options["commit_hook"] = "save"
    return FlowDefinition(
        id="flow-step-proof",
        name="step-proof",
        pattern="wizard",
        options=options,
    )


def _context(runtime: MinimalRuntime) -> PatternBuildContext:
    return PatternBuildContext(
        event_engine=runtime.event,
        execution=runtime.execution,
        registries=runtime.registries,
    )


def test_system_bind_and_stop_read_the_system_registries() -> None:
    process: list[str] = []
    register_runtime_binding(lambda _runtime: process.append("process"))
    seen: list[object] = []
    runtime = MinimalRuntime()
    binding = Registry("runtime binding")
    binding.register("probe", lambda shell: seen.append(shell))
    unbinding = Registry("runtime unbinding")
    unbinding.register("probe", lambda: seen.append("unbind"))
    runtime.registries.install("runtime_binding", binding)
    runtime.registries.install("runtime_unbinding", unbinding)
    try:
        runtime.start(drivers=bind_memory(), structure_definition_id="local.embedded")
        assert seen == [runtime]
        assert process == []
        runtime.stop()
        assert seen == [runtime, "unbind"]
        assert process == []
    finally:
        clear_runtime_binding()
        if runtime.is_started:
            runtime.stop()


def test_kv_uses_the_runtime_storage() -> None:
    def boom() -> None:
        raise AssertionError("process runtime")

    register_runtime_accessor(boom)
    first = MinimalRuntime()
    second = MinimalRuntime()
    for runtime in (first, second):
        providers = Registry("provider")
        providers.register("kv", KvProvider)
        runtime.registries.install("provider", providers)
        runtime.start(drivers=bind_memory(), structure_definition_id="local.embedded")
    try:
        put = first.invoke_resource(
            provider="kv",
            action="put",
            resource_id="todos/list",
            params={"namespace": "palm", "backend": "auto", "value": ["milk"]},
        )
        assert put.success, put.error
        assert put.data["backend"] == "storage"
        memory_key = build_memory_key("palm", "todos/list")
        storage_key = build_storage_key("palm", "todos/list")
        assert get_memory_kv_store().get(memory_key) is None
        assert first.storage.get(storage_key) == ["milk"]
        assert second.storage.get(storage_key) is None
        got = second.invoke_resource(
            provider="kv",
            action="get",
            resource_id="todos/list",
            params={"namespace": "palm", "backend": "auto", "default": []},
        )
        assert got.success, got.error
        assert got.data["value"] == []
    finally:
        clear_runtime_binding()
        for runtime in (first, second):
            if runtime.is_started:
                runtime.stop()


def test_wizard_build_reads_the_system_step_registry() -> None:
    runtime = MinimalRuntime()
    registries = runtime.registries
    registries.install("pattern", Registry("pattern"))
    registries.install("pattern_builder", Registry("pattern builder"))
    registries.install("wizard_step", Registry("wizard step"))
    register_wizard(registries)
    process_steps = default_wizard_step_registry()
    process_steps.clear()
    try:
        runtime.start(drivers=bind_memory(), structure_definition_id="local.embedded")
        pattern = build_pattern(_flow(), context=_context(runtime))
        assert pattern.config.steps[0].step_kind == "resource"
    finally:
        register_builtin_wizard_step_kinds()
        if runtime.is_started:
            runtime.stop()


def test_wizard_build_requires_the_step_registry() -> None:
    runtime = MinimalRuntime()
    registries = runtime.registries
    registries.install("pattern", Registry("pattern"))
    registries.install("pattern_builder", Registry("pattern builder"))
    register_wizard(registries)
    runtime.start(drivers=bind_memory(), structure_definition_id="local.embedded")
    try:
        with pytest.raises(RuntimeError, match="wizard_step registry"):
            build_pattern(_flow(), context=_context(runtime))
    finally:
        runtime.stop()


def test_commit_flow_requires_the_commit_registry() -> None:
    runtime = MinimalRuntime()
    registries = runtime.registries
    registries.install("pattern", Registry("pattern"))
    registries.install("pattern_builder", Registry("pattern builder"))
    registries.install("wizard_step", Registry("wizard step"))
    register_wizard(registries)
    runtime.start(drivers=bind_memory(), structure_definition_id="local.embedded")
    try:
        with pytest.raises(RuntimeError, match="commit registry"):
            build_pattern(_flow(include_commit=True), context=_context(runtime))
    finally:
        runtime.stop()
