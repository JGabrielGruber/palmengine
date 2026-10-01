"""Instance create, update, and resume read the system registry (0.72.11).

The persistence hook and resume read ``instance_sync`` on that runtime.
A missing pattern name raises. The process-wide instance-sync tables are not
a fallback. A runtime that does not install the table records empty fields.
"""

from __future__ import annotations

from typing import Any

import pytest
from bundles.minimal.bind import bind_memory
from bundles.minimal.runtime import MinimalRuntime
from plugins.patterns.wizard.registry import register as register_wizard

from palm.common.patterns._registry import get_instance_fields, register_instance_sync
from palm.common.patterns.build_context import PatternBuildContext
from palm.common.persistence.instance_sync import InstanceSyncHooks
from palm.core.exceptions import RegistryError
from palm.core.orchestration import Job
from palm.core.registry import Registry
from palm.definitions.flow import FlowDefinition
from palm.instances import ProcessInstance
from palm.states import BlackboardState
from palm.system.executions.flow_submission import prepare_resume_submission


def _flow() -> FlowDefinition:
    return FlowDefinition(
        id="flow-sync-proof",
        name="sync-proof",
        pattern="wizard",
        options={
            "include_commit": False,
            "include_summary": False,
            "steps": ["ask"],
        },
    )


def _hooks(tag: str) -> InstanceSyncHooks:
    def fields(job: Job) -> tuple[str | None, dict[str, Any]]:
        del job
        return tag, {"who": tag}

    def resume(
        instance: ProcessInstance,
        executable: Any,
        state: BlackboardState,
    ) -> BlackboardState:
        del instance, executable
        state.set("resumed", tag)
        return state

    return InstanceSyncHooks(fields=fields, resume=resume)


def _process_fields(job: Job) -> tuple[str | None, dict[str, Any]]:
    del job
    return "P", {"who": "P"}


def _process_resume(
    instance: ProcessInstance,
    executable: Any,
    state: BlackboardState,
) -> BlackboardState:
    del instance, executable
    state.set("resumed", "P")
    return state


def _install(runtime: MinimalRuntime, hooks: InstanceSyncHooks | None) -> Registry[Any] | None:
    registries = runtime.registries
    registries.install("pattern", Registry("pattern"))
    registries.install("pattern_builder", Registry("pattern builder"))
    registries.install("wizard_step", Registry("wizard step"))
    table: Registry[Any] | None = None
    if hooks is not None:
        table = Registry("instance sync")
        registries.install("instance_sync", table)
    register_wizard(registries)
    if table is not None and hooks is not None:
        table.register("wizard", hooks)
    return table


def _start(runtime: MinimalRuntime) -> None:
    runtime.start(drivers=bind_memory(), structure_definition_id="local.embedded")


def _submitted(runtime: MinimalRuntime) -> tuple[str | None, Any]:
    job = runtime.submit_flow(_flow())
    instance_id = job.metadata.get("instance_id")
    assert isinstance(instance_id, str)
    instance = runtime.instances.get(instance_id)
    submission = prepare_resume_submission(
        instance,
        build_ctx=PatternBuildContext(
            event_engine=runtime.event,
            execution=runtime.execution,
            registries=runtime.registries,
        ),
    )
    return instance.current_step_slug, submission.state.get("resumed")


def _stop(*runtimes: MinimalRuntime) -> None:
    for runtime in runtimes:
        if runtime.is_started:
            runtime.stop()


@pytest.fixture
def _process_wizard_hooks() -> Any:
    import palm.common.patterns._registry as registry

    with registry._lock:
        saved_fields = dict(registry._instance_fields)
        saved_resume = dict(registry._resume_handlers)
    register_instance_sync("wizard", fields=_process_fields, resume=_process_resume)
    try:
        yield
    finally:
        with registry._lock:
            registry._instance_fields.clear()
            registry._instance_fields.update(saved_fields)
            registry._resume_handlers.clear()
            registry._resume_handlers.update(saved_resume)


def test_instance_sync_reads_the_system_registry(_process_wizard_hooks: None) -> None:
    del _process_wizard_hooks
    first = MinimalRuntime()
    second = MinimalRuntime()
    _install(first, _hooks("A"))
    _install(second, _hooks("B"))
    try:
        _start(first)
        _start(second)
        assert _submitted(first) == ("A", "A")
        assert _submitted(second) == ("B", "B")
        assert get_instance_fields("wizard") is _process_fields
    finally:
        _stop(first, second)


def test_instance_sync_ignores_the_process_table(_process_wizard_hooks: None) -> None:
    del _process_wizard_hooks
    runtime = MinimalRuntime()
    _install(runtime, None)
    try:
        _start(runtime)
        assert _submitted(runtime) == (None, None)
        assert get_instance_fields("wizard") is _process_fields
    finally:
        _stop(runtime)


def test_instance_sync_requires_the_pattern_name() -> None:
    runtime = MinimalRuntime()
    table = _install(runtime, _hooks("A"))
    assert table is not None
    table.drop("wizard")
    try:
        _start(runtime)
        with pytest.raises(RegistryError, match="wizard"):
            runtime.submit_flow(_flow())
    finally:
        _stop(runtime)
