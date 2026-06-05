"""Integration tests for EmbeddedRuntime orchestration wiring."""

from __future__ import annotations

import pytest

from palm.core.behavior_tree import BasePattern, PatternStatus
from palm.core.context import BaseState
from palm.core.orchestration import JobStatus
from palm.patterns.wizard import WizardConfig, WizardEventType, WizardKeys, WizardStepConfig
from palm.runtimes.embedded import EmbeddedRuntime
from palm.states import BlackboardState


def _two_step_config() -> WizardConfig:
    return WizardConfig(
        steps=(
            WizardStepConfig(slug="name", title="Name", prompt="Your name?"),
            WizardStepConfig(slug="confirm", title="Confirm", prompt="Proceed?"),
        ),
    )


@pytest.fixture
def runtime() -> EmbeddedRuntime:
    rt = EmbeddedRuntime()
    rt.start()
    yield rt
    rt.stop()


def test_embedded_runtime_starts_and_stops() -> None:
    rt = EmbeddedRuntime()
    assert not rt.is_started
    rt.start()
    assert rt.is_started
    assert rt.orchestration.is_running()
    assert rt.context.is_initialized
    assert rt.event.is_initialized
    rt.stop()
    assert not rt.is_started
    assert not rt.orchestration.is_running()


def test_embedded_wizard_flow_to_completion(runtime: EmbeddedRuntime) -> None:
    events: list[str] = []
    runtime.event.subscribe("*", lambda e: events.append(e.type))

    job = runtime.submit_wizard(name="onboard", config=_two_step_config())
    assert job.status == JobStatus.WAITING_FOR_INPUT
    assert runtime.current_wizard_step(job.id) == "name"

    runtime.provide_input(job.id, "Ada")
    assert job.status == JobStatus.WAITING_FOR_INPUT
    assert runtime.current_wizard_step(job.id) == "confirm"

    runtime.provide_input(job.id, "yes")
    assert job.status == JobStatus.SUCCEEDED
    assert runtime.wizard_answers(job.id) == {"name": "Ada", "confirm": "yes"}
    assert job.state.get(WizardKeys.COMPLETED) is True
    assert WizardEventType.COMPLETED in events


def test_embedded_submit_wizard_uses_shared_blackboard(runtime: EmbeddedRuntime) -> None:
    state = BlackboardState({"trace": True})
    job = runtime.submit_wizard(config=_two_step_config(), state=state)
    assert job.state is state
    assert runtime.context.current_state is state


def test_provide_input_requires_started() -> None:
    rt = EmbeddedRuntime()
    job = None
    rt.start()
    job = rt.submit_wizard(steps=1)
    rt.stop()
    with pytest.raises(RuntimeError, match="not started"):
        rt.provide_input(job.id, "x")


class _InstantPattern(BasePattern):
    def tick(self, state: BaseState) -> PatternStatus:
        return PatternStatus.SUCCESS


def test_provide_input_rejects_non_wizard_job(runtime: EmbeddedRuntime) -> None:
    job = runtime.orchestration.submit(_InstantPattern(name="noop"))
    assert job.status == JobStatus.SUCCEEDED
    with pytest.raises(TypeError, match="not a wizard"):
        runtime.provide_input(job.id, "value")
