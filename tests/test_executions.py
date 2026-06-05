"""Tests for definition-driven execution (executions layer)."""

from __future__ import annotations

import pytest

from palm.core.behavior_tree import BasePattern
from palm.core.orchestration import Job, JobStatus
from palm.definitions import FlowDefinition, ProcessDefinition
from palm.executions import (
    DefinitionBuildError,
    DefinitionExecutor,
    build_pattern,
    wizard_config_from_options,
)
from palm.patterns.wizard import WizardEventType, WizardKeys, WizardPattern
from palm.runtimes.embedded import EmbeddedRuntime


def _onboard_flow() -> FlowDefinition:
    return FlowDefinition(
        name="onboard",
        pattern="wizard",
        options={
            "steps": [
                {"slug": "name", "title": "Name", "prompt": "Your name?"},
                {"slug": "confirm", "title": "Confirm", "prompt": "Proceed?"},
            ],
            "allow_backtrack": True,
        },
    )


@pytest.fixture
def runtime() -> EmbeddedRuntime:
    rt = EmbeddedRuntime()
    rt.start()
    yield rt
    rt.stop()


def test_build_pattern_wizard_from_flow() -> None:
    pattern = build_pattern(_onboard_flow())
    assert isinstance(pattern, WizardPattern)
    assert pattern.config.step_count == 2


def test_wizard_config_from_slug_list() -> None:
    config = wizard_config_from_options({"steps": ["a", "b"]})
    assert config.steps[0].slug == "a"
    assert config.steps[1].slug == "b"


def test_definition_executor_requires_started() -> None:
    rt = EmbeddedRuntime()
    executor = DefinitionExecutor(rt)
    with pytest.raises(RuntimeError, match="not started"):
        executor.submit_flow(_onboard_flow())


def test_submit_flow_wizard_to_completion(runtime: EmbeddedRuntime) -> None:
    events: list[str] = []
    runtime.event.subscribe("*", lambda e: events.append(e.type))

    job = runtime.submit_flow(_onboard_flow())
    assert job.metadata["pattern"] == "wizard"
    assert job.metadata["flow"] == "onboard"
    assert job.status == JobStatus.WAITING_FOR_INPUT
    assert runtime.current_wizard_step(job.id) == "name"

    runtime.provide_input(job.id, "Ada")
    assert job.status == JobStatus.WAITING_FOR_INPUT
    assert runtime.current_wizard_step(job.id) == "confirm"

    runtime.provide_input(job.id, "yes")
    assert job.status == JobStatus.SUCCEEDED
    assert runtime.wizard_answers(job.id) == {"name": "Ada", "confirm": "yes"}
    assert WizardEventType.COMPLETED in events


def test_submit_process_single_flow(runtime: EmbeddedRuntime) -> None:
    process = ProcessDefinition(
        name="onboarding",
        flows=[_onboard_flow()],
        metadata={"team": "platform"},
    )
    job = runtime.submit_process(process)
    assert isinstance(job, Job)
    assert job.metadata["process"] == "onboarding"
    assert job.metadata["process_metadata"] == {"team": "platform"}


def test_submit_process_multiple_flows(runtime: EmbeddedRuntime) -> None:
    process = ProcessDefinition(
        name="pipeline",
        flows=[
            FlowDefinition(name="extract", pattern="etl"),
            FlowDefinition(name="graph", pattern="dag"),
        ],
    )
    result = runtime.submit_process(process)
    assert isinstance(result, list)
    assert len(result) == 2
    assert result[0].status == JobStatus.SUCCEEDED
    assert result[1].status == JobStatus.SUCCEEDED


def test_submit_process_empty_raises(runtime: EmbeddedRuntime) -> None:
    with pytest.raises(DefinitionBuildError, match="no flows"):
        runtime.submit_process(ProcessDefinition(name="empty", flows=[]))


def test_build_unknown_pattern_raises() -> None:
    flow = FlowDefinition(name="x", pattern="nonexistent")
    with pytest.raises(DefinitionBuildError):
        build_pattern(flow)


def test_builder_rejects_unsupported_options() -> None:
    flow = FlowDefinition(name="dag", pattern="dag", options={"extra": True})
    with pytest.raises(DefinitionBuildError, match="does not support"):
        build_pattern(flow)


def test_wizard_via_process_definition(runtime: EmbeddedRuntime) -> None:
    process = ProcessDefinition(
        name="quick",
        flows=[
            FlowDefinition(
                name="two-step",
                pattern="wizard",
                options={"steps": 2},
            )
        ],
    )
    job = runtime.submit_process(process)
    assert isinstance(job, Job)
    assert isinstance(job.executable, BasePattern)
    runtime.provide_input(job.id, "first")
    runtime.provide_input(job.id, "second")
    assert job.status == JobStatus.SUCCEEDED
    assert job.state.get(WizardKeys.COMPLETED) is True