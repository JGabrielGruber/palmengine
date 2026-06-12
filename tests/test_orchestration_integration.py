"""Orchestration integration tests — patterns and external backends (not pure core)."""

from __future__ import annotations

from palm.backends.behavior_tree import BehaviorTreeRunner
from palm.core.event import EventEngine
from palm.core.orchestration import JobStatus, OrchestrationEngine
from palm.patterns.wizard import (
    WizardConfig,
    WizardEventType,
    WizardKeys,
    WizardPattern,
    WizardStepConfig,
)
from palm.states import BlackboardState
from tests.core.fakes.mode import TestMode


def _wizard_config() -> WizardConfig:
    return WizardConfig(
        steps=(
            WizardStepConfig(slug="name", title="Name", prompt="Name?"),
            WizardStepConfig(
                slug="role",
                title="Role",
                prompt="Role?",
                field_type="choice",
                choices=("dev", "mgr"),
            ),
        ),
        allow_backtrack=True,
    )


def test_wizard_job_via_behavior_tree_runner(event_engine: EventEngine) -> None:
    events: list[tuple[str, dict]] = []
    event_engine.subscribe("*", lambda e: events.append((e.type, dict(e.payload))))

    state = BlackboardState()
    wizard = WizardPattern(
        name="onboard",
        config=_wizard_config(),
        event_engine=event_engine,
    )

    mode = TestMode(runner=BehaviorTreeRunner())
    engine = OrchestrationEngine()
    engine.initialize(scheduler=mode, event_engine=event_engine)
    engine.start()

    job = engine.submit(wizard, state=state)
    assert job.status == JobStatus.WAITING_FOR_INPUT
    assert wizard.current_step_slug(state) == "name"

    wizard.provide_input(state, "Ada")
    engine.resume_job(job.id)
    assert job.status == JobStatus.WAITING_FOR_INPUT
    assert wizard.current_step_slug(state) == "role"

    wizard.provide_input(state, "dev")
    engine.resume_job(job.id)
    assert job.status == JobStatus.SUCCEEDED
    assert wizard.answers(state) == {"name": "Ada", "role": "dev"}
    assert state.get(WizardKeys.COMPLETED) is True
    assert any(e[0] == WizardEventType.COMPLETED for e in events)

    engine.stop()
    engine.shutdown()
