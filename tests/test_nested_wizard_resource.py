"""Nested wizard compositional flows via palm provider wait_mode."""

from __future__ import annotations

import plugins.providers  # noqa: F401 — register providers
import pytest
from bundles.standard.runtimes.embedded import EmbeddedRuntime
from plugins.patterns.wizard import WizardKeys
from plugins.providers.palm.bindings.runtimes.wiring import clear_palm_runtime
from plugins.providers.palm.provider import PalmProvider

from palm.core.orchestration import JobStatus
from palm.definitions import FlowDefinition, ResourceDefinition


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
    rt.start(storage_backend="memory")
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
    assert result.data.get("nested_park") is True
    assert result.data.get("child_job_id") == result.data["job_id"]
    assert result.metadata["wait_mode"] == "until_input"
    assert result.metadata.get("nested_park") is True


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


def test_parent_wizard_suspends_until_child_completes(runtime: EmbeddedRuntime) -> None:
    from palm.core.wait import (
        STATE_KEY_WAIT_INTERESTS,
        WAIT_KIND_JOB,
        has_open_waits,
        list_wait_interests,
    )

    parent_job = runtime.submit_flow("parent-wizard")
    runtime.wait_until_idle(timeout=5)

    assert parent_job.status == JobStatus.WAITING_FOR_INPUT
    assert parent_job.state.get(WizardKeys.CURRENT_STEP) == "spawn_child"

    from plugins.patterns.wizard.bindings.resource.nested_park import nested_park_interest

    park = nested_park_interest(parent_job.state)
    assert park is not None
    child_job_id = park.target_id
    assert child_job_id

    assert has_open_waits(parent_job.state)
    interests = list_wait_interests(parent_job.state)
    assert len(interests) == 1
    assert interests[0].kind == WAIT_KIND_JOB
    assert interests[0].target_id == str(child_job_id)
    assert interests[0].meta.get("source") == "nested_wizard"
    assert interests[0].meta.get("step_slug") == "spawn_child"
    raw = parent_job.state.get(STATE_KEY_WAIT_INTERESTS)
    assert isinstance(raw, list) and raw[0]["target_id"] == str(child_job_id)
    child_job = runtime.get_job(str(child_job_id))
    assert child_job.status == JobStatus.WAITING_FOR_INPUT
    assert child_job.metadata.get("__palm:parent_job_id") == parent_job.id

    answers = parent_job.state.get(WizardKeys.ANSWERS) or {}
    assert "child_job" not in answers

    runtime.provide_input(child_job_id, "nested answer")
    runtime.wait_until_idle(timeout=5)

    child_job = runtime.get_job(str(child_job_id))
    assert child_job.status == JobStatus.SUCCEEDED

    parent_job = runtime.get_job(parent_job.id)
    assert parent_job.status == JobStatus.SUCCEEDED
    answers = parent_job.state.get(WizardKeys.ANSWERS) or {}
    assert isinstance(answers.get("child_job"), dict)
    assert answers["child_job"]["status"] == JobStatus.SUCCEEDED.value
    assert nested_park_interest(parent_job.state) is None
    assert not has_open_waits(parent_job.state)
