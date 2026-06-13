"""Tests for QueuedScheduler background job driving."""

from __future__ import annotations

import pytest

from palm.backends.behavior_tree import BehaviorTreeRunner
from palm.common.runtimes.schedulers import QueuedScheduler
from palm.core.context import ContextEngine
from palm.core.event import EventEngine
from palm.core.orchestration import JobStatus, OrchestrationEngine
from palm.patterns.wizard import WizardConfig, WizardStepConfig
from tests.core.fakes.runner import TestRunner


def _two_step_config() -> WizardConfig:
    return WizardConfig(
        steps=(
            WizardStepConfig(slug="name", title="Name", prompt="Your name?"),
            WizardStepConfig(slug="confirm", title="Confirm", prompt="Proceed?"),
        ),
    )


@pytest.fixture
def queued_engine() -> OrchestrationEngine:
    scheduler = QueuedScheduler(runner=TestRunner())
    events = EventEngine()
    context = ContextEngine()
    events.initialize()
    context.initialize()
    engine = OrchestrationEngine()
    engine.initialize(
        scheduler=scheduler,
        event_engine=events,
        context_engine=context,
    )
    engine.start()
    yield engine
    engine.stop()
    scheduler.shutdown()
    context.shutdown()
    events.shutdown()


def test_queued_scheduler_drives_job_in_background(queued_engine: OrchestrationEngine) -> None:
    scheduler = queued_engine.scheduler
    assert isinstance(scheduler, QueuedScheduler)

    job = queued_engine.submit({"steps": 1, "final_status": "SUCCEEDED", "result": "ok"})
    assert job.status == JobStatus.PENDING
    assert scheduler.wait_until_idle()
    assert job.status == JobStatus.SUCCEEDED
    assert job.result == "ok"


def test_queued_scheduler_wizard_flow() -> None:
    from palm.common import build_pattern
    from palm.definitions.flow import FlowDefinition

    scheduler = QueuedScheduler(runner=BehaviorTreeRunner())
    events = EventEngine()
    context = ContextEngine()
    events.initialize()
    context.initialize()
    queued_engine = OrchestrationEngine()
    queued_engine.initialize(
        scheduler=scheduler,
        event_engine=events,
        context_engine=context,
    )
    queued_engine.start()

    flow = FlowDefinition(
        name="onboard",
        pattern="wizard",
        options={"config": _two_step_config()},
    )
    pattern = build_pattern(flow)
    job = queued_engine.submit(pattern)
    assert scheduler.wait_until_idle()
    assert job.status == JobStatus.WAITING_FOR_INPUT

    queued_engine.deliver_input(job.id, "Ada")
    assert scheduler.wait_until_idle()
    assert job.status == JobStatus.WAITING_FOR_INPUT

    queued_engine.deliver_input(job.id, "yes")
    assert scheduler.wait_until_idle()
    assert job.status == JobStatus.SUCCEEDED

    queued_engine.stop()
    scheduler.shutdown()
    context.shutdown()
    events.shutdown()
