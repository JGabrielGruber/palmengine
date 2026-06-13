"""Tests for DaemonRuntime and shared runtime wiring."""

from __future__ import annotations

import pytest

from palm.common.runtimes.host import RuntimeHost
from palm.common.runtimes.schedulers import InlineScheduler, QueuedScheduler
from palm.common.runtimes.wiring import resolve_scheduler
from palm.core.orchestration import JobStatus
from palm.patterns.wizard import WizardConfig, WizardStepConfig
from palm.runtimes.daemon import DaemonRuntime
from palm.runtimes.embedded import EmbeddedRuntime
from tests.core.fakes.runner import TestRunner


def _two_step_config() -> WizardConfig:
    return WizardConfig(
        steps=(
            WizardStepConfig(slug="name", title="Name", prompt="Your name?"),
            WizardStepConfig(slug="confirm", title="Confirm", prompt="Proceed?"),
        ),
    )


@pytest.fixture
def daemon() -> DaemonRuntime:
    rt = DaemonRuntime()
    rt.start()
    yield rt
    rt.stop()


def test_daemon_runtime_satisfies_runtime_host() -> None:
    rt = DaemonRuntime()
    assert isinstance(rt, RuntimeHost)


def test_daemon_defaults_to_queued_scheduler(daemon: DaemonRuntime) -> None:
    assert isinstance(daemon.orchestration.scheduler, QueuedScheduler)


def test_embedded_defaults_to_inline_scheduler() -> None:
    rt = EmbeddedRuntime()
    rt.start()
    try:
        assert isinstance(rt.orchestration.scheduler, InlineScheduler)
    finally:
        rt.stop()


def test_resolve_scheduler_policy_strings() -> None:
    inline = resolve_scheduler({"scheduler": "inline", "runner": TestRunner()})
    queued = resolve_scheduler({"scheduler": "queued", "runner": TestRunner()})
    assert isinstance(inline, InlineScheduler)
    assert isinstance(queued, QueuedScheduler)


def test_daemon_wizard_flow_to_completion(daemon: DaemonRuntime) -> None:
    job = daemon.submit_wizard(name="onboard", config=_two_step_config())
    assert daemon.wait_until_idle()
    assert job.status == JobStatus.WAITING_FOR_INPUT
    assert daemon.current_wizard_step(job.id) == "name"

    daemon.provide_input(job.id, "Ada")
    assert daemon.wait_until_idle()
    assert job.status == JobStatus.WAITING_FOR_INPUT

    daemon.provide_input(job.id, "yes")
    assert daemon.wait_until_idle()
    assert job.status == JobStatus.SUCCEEDED
    assert daemon.wizard_answers(job.id) == {"name": "Ada", "confirm": "yes"}


def test_embedded_accepts_scheduler_policy_override() -> None:
    rt = EmbeddedRuntime()
    rt.start(scheduler="queued", runner=TestRunner())
    try:
        assert isinstance(rt.orchestration.scheduler, QueuedScheduler)
        job = rt.orchestration.submit({"steps": 1, "final_status": "SUCCEEDED"})
        assert isinstance(rt.orchestration.scheduler, QueuedScheduler)
        assert rt.orchestration.scheduler.wait_until_idle()
        assert job.status == JobStatus.SUCCEEDED
    finally:
        rt.stop()
