"""The state snapshot hook reads the system registry (0.72.12).

Hook install passes ``instance_sync`` into the snapshot hook when snapshots
are enabled. A missing pattern name raises. The process field table is not a
fallback. A runtime that does not install the table records an empty step.
"""

from __future__ import annotations

from typing import Any

import pytest
from bundles.minimal.bind import bind_memory
from bundles.minimal.runtime import MinimalRuntime
from plugins.patterns.wizard.registry import register as register_wizard

from palm.common.patterns._registry import get_instance_fields, register_instance_sync
from palm.common.persistence.instance_sync import InstanceSyncHooks
from palm.core.exceptions import RegistryError
from palm.core.orchestration import Job, JobStatus, OrchestrationEngine
from palm.core.registry import Registry
from palm.definitions.flow import FlowDefinition
from palm.instances import ProcessInstance, StateSnapshot
from palm.states import BlackboardState
from palm.system.runtime.job_hooks.state_snapshot import StateSnapshotHook


def _flow() -> FlowDefinition:
    return FlowDefinition(
        id="flow-snap-proof",
        name="snap-proof",
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
    runtime.start(
        drivers=bind_memory(),
        structure_definition_id="local.embedded",
        enable_state_snapshot=True,
    )


def _recorded(runtime: MinimalRuntime) -> tuple[str | None, dict[str, Any]]:
    job = runtime.submit_flow(_flow())
    instance_id = job.metadata.get("instance_id")
    assert isinstance(instance_id, str)
    snapshots = runtime.instances.list_state_snapshots(instance_id)
    assert snapshots
    latest = snapshots[-1]
    return latest.current_step_slug, dict(latest.runtime_position)


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


def test_state_snapshot_reads_the_system_registry(_process_wizard_hooks: None) -> None:
    del _process_wizard_hooks
    first = MinimalRuntime()
    second = MinimalRuntime()
    _install(first, _hooks("A"))
    _install(second, _hooks("B"))
    try:
        _start(first)
        _start(second)
        assert _recorded(first) == ("A", {"who": "A"})
        assert _recorded(second) == ("B", {"who": "B"})
        assert get_instance_fields("wizard") is _process_fields
    finally:
        _stop(first, second)


def test_state_snapshot_ignores_the_process_table(_process_wizard_hooks: None) -> None:
    del _process_wizard_hooks
    runtime = MinimalRuntime()
    _install(runtime, None)
    try:
        _start(runtime)
        assert _recorded(runtime) == (None, {})
        assert get_instance_fields("wizard") is _process_fields
    finally:
        _stop(runtime)


def test_state_snapshot_requires_the_pattern_name() -> None:
    table: Registry[Any] = Registry("instance sync")
    job = Job(
        id="job-missing",
        executable={},
        metadata={"instance_id": "inst-missing", "pattern": "wizard"},
    )
    job.status = JobStatus.WAITING_FOR_INPUT
    with pytest.raises(RegistryError, match="wizard"):
        StateSnapshot.now(job, sync=table)

    class _Ready:
        def get(self, instance_id: str) -> ProcessInstance:
            del instance_id
            return ProcessInstance(
                instance_id="inst-missing",
                job_id="job-missing",
                status=JobStatus.WAITING_FOR_INPUT.value,
                state_snapshot={},
                flow_definition={},
                pattern="wizard",
            )

        def append_state_snapshot(self, *args: object, **kwargs: object) -> None:
            raise AssertionError("missing pattern name must raise before append")

    hook = StateSnapshotHook(_Ready(), sync=table)
    with pytest.raises(RegistryError, match="wizard"):
        hook.on_job_status_changed(OrchestrationEngine(), job)
