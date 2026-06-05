"""Tests for the orchestration engine (TestBackend + optional BT integration)."""

from __future__ import annotations

import pytest

from palm.backends.behavior_tree import BehaviorTreeBackend
from palm.core.context import ContextEngine
from palm.core.event import EventEngine
from palm.core.orchestration import (
    Job,
    JobStatus,
    OrchestrationEngine,
    OrchestrationEventType,
    TestMode,
)
from palm.core.orchestration.exceptions import JobNotFoundError, OrchestratorError
from palm.patterns.wizard import (
    WizardConfig,
    WizardEventType,
    WizardKeys,
    WizardPattern,
    WizardStepConfig,
)
from palm.states import BlackboardState


def _engine(*, mode: TestMode | None = None) -> OrchestrationEngine:
    engine = OrchestrationEngine()
    engine.initialize(mode=mode or TestMode())
    engine.start()
    return engine


def test_submit_succeeds_with_test_backend() -> None:
    engine = _engine()
    job = engine.submit({"steps": 1, "final_status": "SUCCEEDED", "result": "ok"})
    assert isinstance(job, Job)
    assert job.status == JobStatus.SUCCEEDED
    assert job.result == "ok"
    engine.stop()


def test_get_job_and_list_by_status() -> None:
    engine = _engine()
    done = engine.submit({"steps": 1, "final_status": "SUCCEEDED"})
    waiting = engine.submit({"steps": 1, "final_status": "WAITING_FOR_INPUT"})
    assert engine.get_job(done.id) is done
    assert done in engine.list_jobs(JobStatus.SUCCEEDED)
    assert waiting in engine.list_jobs(JobStatus.WAITING_FOR_INPUT)
    engine.stop()


def test_unknown_job_raises() -> None:
    engine = _engine()
    with pytest.raises(JobNotFoundError):
        engine.get_job("missing")
    engine.stop()


def test_max_concurrent_jobs_enforced() -> None:
    engine = _engine()
    engine.max_concurrent_jobs = 2
    engine.submit({"steps": 1})
    engine.submit({"steps": 1})
    with pytest.raises(OrchestratorError, match="Maximum concurrent"):
        engine.submit({"steps": 1})
    engine.stop()


def test_waiting_job_resumes_via_provide_input() -> None:
    engine = _engine()
    job = engine.submit({"steps": 1, "final_status": "WAITING_FOR_INPUT"})
    assert job.status == JobStatus.WAITING_FOR_INPUT
    engine.provide_input(job.id, "answer", 42)
    assert job.status == JobStatus.SUCCEEDED
    assert job.state.get("answer") == 42
    engine.stop()


def test_orchestration_events_via_event_engine() -> None:
    events: list[str] = []
    bus = EventEngine()
    bus.initialize()
    bus.subscribe("*", lambda e: events.append(e.type))

    engine = OrchestrationEngine()
    engine.initialize(mode=TestMode(), event_engine=bus)
    engine.start()
    job = engine.submit({"steps": 1, "final_status": "SUCCEEDED"})
    engine.stop()
    engine.shutdown()

    assert OrchestrationEventType.ENGINE_STARTED in events
    assert OrchestrationEventType.JOB_SUBMITTED in events
    assert OrchestrationEventType.JOB_STATUS_CHANGED in events
    assert OrchestrationEventType.JOB_COMPLETED in events
    assert job.status == JobStatus.SUCCEEDED


def test_context_engine_binds_job_state() -> None:
    ctx = ContextEngine()
    ctx.initialize()
    engine = OrchestrationEngine()
    engine.initialize(mode=TestMode(), context_engine=ctx)
    engine.start()

    state = BlackboardState({"seed": 1})
    job = engine.submit({"steps": 1, "final_status": "SUCCEEDED"}, state=state)
    assert ctx.current_state is state
    assert ctx.get("job_id") == job.id
    engine.stop()
    engine.shutdown()
    ctx.shutdown()


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


def test_wizard_job_via_behavior_tree_backend() -> None:
    events: list[tuple[str, dict]] = []
    bus = EventEngine()
    bus.initialize()
    bus.subscribe("*", lambda e: events.append((e.type, dict(e.payload))))

    state = BlackboardState()
    wizard = WizardPattern(
        name="onboard",
        config=_wizard_config(),
        event_engine=bus,
    )

    mode = TestMode(backend=BehaviorTreeBackend())
    engine = OrchestrationEngine()
    engine.initialize(mode=mode, event_engine=bus)
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
    bus.shutdown()