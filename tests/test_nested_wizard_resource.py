"""Nested wizard compositional flows via palm provider wait_mode."""

from __future__ import annotations

import pytest

import palm.providers  # noqa: F401 — register providers
from palm.core.orchestration import JobStatus
from palm.definitions import FlowDefinition, ResourceDefinition
from palm.patterns.wizard import WizardKeys
from palm.providers.palm.provider import PalmProvider
from palm.providers.palm.wiring import clear_palm_runtime
from palm.runtimes.embedded import EmbeddedRuntime


def _child_wizard_flow() -> FlowDefinition:
    return FlowDefinition(
        id="flow-child-wizard",
        name="child-wizard",
        pattern="wizard",
        options={
            "steps": [
                {"slug": "question", "title": "Question", "prompt": "Child question?"},
            ],
        },
    )


def _parent_wizard_flow() -> FlowDefinition:
    return FlowDefinition(
        id="flow-parent-wizard",
        name="parent-wizard",
        pattern="wizard",
        options={
            "steps": [
                {
                    "slug": "spawn_child",
                    "title": "Spawn Child Wizard",
                    "step_kind": "resource",
                    "resource_ref": "submit-child-wizard",
                    "output_key": "child_job",
                },
            ],
        },
    )


def _submit_child_resource() -> ResourceDefinition:
    return ResourceDefinition(
        id="resource-submit-child-wizard",
        name="submit-child-wizard",
        provider="palm",
        action="submit_flow",
        resource_id="flow:child-wizard",
        params={
            "wait": True,
            "wait_mode": "until_input",
            "timeout_seconds": 5,
        },
    )


@pytest.fixture
def runtime() -> EmbeddedRuntime:
    rt = EmbeddedRuntime()
    rt.start()
    rt.repository.save_flow(_child_wizard_flow())
    rt.repository.save_flow(_parent_wizard_flow())
    rt.repository.save_resource(_submit_child_resource())
    yield rt
    rt.stop()
    clear_palm_runtime()


def _palm_provider() -> PalmProvider:
    provider = PalmProvider(name="palm")
    provider.connect()
    return provider


def test_palm_provider_wait_mode_until_input(runtime: EmbeddedRuntime) -> None:
    provider = _palm_provider()
    result = provider.invoke(
        "submit_flow",
        resource_id="flow:child-wizard",
        params={"wait_mode": "until_input", "timeout_seconds": 5},
    )
    assert result.success is True
    assert result.data["status"] == JobStatus.WAITING_FOR_INPUT.value
    assert result.data["job_id"]
    assert result.data.get("waiting_for_child_wizard") is True
    assert result.data.get("child_job_id") == result.data["job_id"]
    assert result.metadata["wait_mode"] == "until_input"
    assert result.metadata.get("waiting_for_child_wizard") is True


def test_palm_provider_until_terminal_timeout_message(runtime: EmbeddedRuntime) -> None:
    provider = _palm_provider()
    result = provider.invoke(
        "submit_flow",
        resource_id="flow:child-wizard",
        params={"wait": True, "wait_timeout": 0.2},
    )
    assert result.success is False
    assert result.error is not None
    assert "wait_mode='until_input'" in result.error
    assert "WAITING_FOR_INPUT" in result.error or "interactive input" in result.error


def test_parent_wizard_resource_step_until_input(runtime: EmbeddedRuntime) -> None:
    job = runtime.submit_flow("parent-wizard")
    runtime.wait_until_idle(timeout=5)

    assert job.status != JobStatus.FAILED
    answers = job.state.get(WizardKeys.ANSWERS) or {}
    child_output = answers.get("child_job")
    assert isinstance(child_output, dict)
    assert child_output["status"] == JobStatus.WAITING_FOR_INPUT.value
    assert child_output.get("waiting_for_child_wizard") is True
    assert child_output.get("child_job_id")

    child_job = runtime.get_job(str(child_output["child_job_id"]))
    assert child_job.status == JobStatus.WAITING_FOR_INPUT