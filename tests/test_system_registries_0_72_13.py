"""Interactive continue reads the system registry (0.72.13).

Input and backtrack take the ``interactive_runtime`` table the caller passes.
A missing pattern name raises. The process interactive-runtime table is not a
fallback. A runtime that does not install the table does not read that process
table.
"""

from __future__ import annotations

from typing import Any

import pytest
from bundles.minimal.bind import bind_memory
from bundles.minimal.runtime import MinimalRuntime
from plugins.patterns.wizard.registry import register as register_wizard

from palm.common.interactive_runtime import (
    previous_interactive_step,
    provide_interactive_input_for_instance,
    request_interactive_backtrack_for_instance,
    require_interactive_job,
)
from palm.common.patterns._registry import (
    InteractiveRuntimeHooks,
    get_interactive_runtime,
    register_interactive_runtime,
)
from palm.core.exceptions import RegistryError
from palm.core.orchestration import Job
from palm.core.registry import Registry
from palm.definitions.flow import FlowDefinition


def _flow() -> FlowDefinition:
    return FlowDefinition(
        id="flow-interactive-proof",
        name="interactive-proof",
        pattern="wizard",
        options={
            "include_commit": False,
            "include_summary": False,
            "steps": ["ask", "next"],
        },
    )


def _hooks(tag: str, seen: list[str]) -> InteractiveRuntimeHooks:
    def is_executable(executable: Any) -> bool:
        del executable
        seen.append(f"{tag}:is")
        return True

    def previous_step(executable: Any, state: Any) -> str:
        del executable, state
        seen.append(f"{tag}:prev")
        return "ask"

    return InteractiveRuntimeHooks(is_executable=is_executable, previous_step=previous_step)


def _process_is_executable(executable: Any) -> bool:
    del executable
    return False


def _process_previous_step(executable: Any, state: Any) -> str:
    del executable, state
    return "P"


def _process_hooks() -> InteractiveRuntimeHooks:
    return InteractiveRuntimeHooks(
        is_executable=_process_is_executable,
        previous_step=_process_previous_step,
    )


def _install(
    runtime: MinimalRuntime,
    hooks: InteractiveRuntimeHooks | None,
) -> Registry[Any] | None:
    registries = runtime.registries
    registries.install("pattern", Registry("pattern"))
    registries.install("pattern_builder", Registry("pattern builder"))
    registries.install("wizard_step", Registry("wizard step"))
    table: Registry[Any] | None = None
    if hooks is not None:
        table = Registry("interactive runtime")
        registries.install("interactive_runtime", table)
    register_wizard(registries)
    if table is not None and hooks is not None:
        table.register("wizard", hooks)
    return table


def _start(runtime: MinimalRuntime) -> None:
    runtime.start(
        drivers=bind_memory(),
        structure_definition_id="local.embedded",
    )


def _waiting(runtime: MinimalRuntime) -> str:
    job = runtime.submit_flow(_flow())
    instance_id = job.metadata.get("instance_id")
    assert isinstance(instance_id, str)
    assert job.status.value == "WAITING_FOR_INPUT"
    return instance_id


def _stop(*runtimes: MinimalRuntime) -> None:
    for runtime in runtimes:
        if runtime.is_started:
            runtime.stop()


@pytest.fixture
def _process_interactive_hooks() -> Any:
    import palm.common.patterns._registry as registry

    with registry._lock:
        saved = dict(registry._interactive_runtime)
    register_interactive_runtime("wizard", _process_hooks())
    try:
        yield
    finally:
        with registry._lock:
            registry._interactive_runtime.clear()
            registry._interactive_runtime.update(saved)


def test_interactive_input_reads_the_system_registry(
    _process_interactive_hooks: None,
) -> None:
    del _process_interactive_hooks
    seen_a: list[str] = []
    seen_b: list[str] = []
    first = MinimalRuntime()
    second = MinimalRuntime()
    _install(first, _hooks("A", seen_a))
    _install(second, _hooks("B", seen_b))
    try:
        _start(first)
        _start(second)
        first_id = _waiting(first)
        second_id = _waiting(second)
        first_hooks = first.registries.require("interactive_runtime")
        second_hooks = second.registries.require("interactive_runtime")

        provide_interactive_input_for_instance(
            first,
            first_id,
            "one",
            hooks=first_hooks,
        )
        provide_interactive_input_for_instance(
            second,
            second_id,
            "one",
            hooks=second_hooks,
        )
        assert seen_a == ["A:is"]
        assert seen_b == ["B:is"]

        _job, target_a = request_interactive_backtrack_for_instance(
            first,
            first_id,
            None,
            hooks=first_hooks,
        )
        _job, target_b = request_interactive_backtrack_for_instance(
            second,
            second_id,
            None,
            hooks=second_hooks,
        )
        assert target_a == "ask"
        assert target_b == "ask"
        assert seen_a == ["A:is", "A:is", "A:prev"]
        assert seen_b == ["B:is", "B:is", "B:prev"]
        assert previous_interactive_step(
            object(),
            object(),
            pattern="wizard",
            hooks=first_hooks,
        ) == "ask"
        assert get_interactive_runtime("wizard") is not None
        assert get_interactive_runtime("wizard").previous_step(object(), object()) == "P"
    finally:
        _stop(first, second)


def test_interactive_runtime_ignores_the_process_table(
    _process_interactive_hooks: None,
) -> None:
    del _process_interactive_hooks
    runtime = MinimalRuntime()
    _install(runtime, None)
    try:
        _start(runtime)
        _waiting(runtime)
        with pytest.raises(RuntimeError, match="interactive_runtime"):
            runtime.registries.require("interactive_runtime")
        process = get_interactive_runtime("wizard")
        assert process is not None
        assert process.previous_step(object(), object()) == "P"
    finally:
        _stop(runtime)


def test_interactive_runtime_requires_the_pattern_name(
    _process_interactive_hooks: None,
) -> None:
    del _process_interactive_hooks
    table: Registry[Any] = Registry("interactive runtime")
    job = Job(id="job-missing", executable=object(), metadata={"pattern": "wizard"})
    with pytest.raises(RegistryError, match="wizard"):
        require_interactive_job(job, "inst-missing", hooks=table)
    with pytest.raises(RegistryError, match="wizard"):
        previous_interactive_step(object(), object(), pattern="wizard", hooks=table)
    assert get_interactive_runtime("wizard") is not None
    assert get_interactive_runtime("wizard").previous_step(object(), object()) == "P"
