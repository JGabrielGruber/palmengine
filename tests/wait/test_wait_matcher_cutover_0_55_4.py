"""WaitMatcher is the sole nested unpark path (no ChildCompletionHook)."""

from __future__ import annotations

import pytest

import plugins.providers  # noqa: F401
from palm.core.orchestration import JobStatus
from palm.core.wait import has_open_waits, list_wait_interests
from palm.definitions import FlowDefinition, ResourceDefinition
from plugins.patterns.wizard import WizardKeys
from plugins.providers.palm.bindings.runtimes.wiring import clear_palm_runtime
from bundles.standard.runtimes.embedded import EmbeddedRuntime


def _child_wizard_flow() -> FlowDefinition:
    return FlowDefinition(
        id="flow-child-wizard-554",
        name="child-wizard-554",
        pattern="wizard",
        options={
            "steps": [
                {"slug": "question", "title": "Question", "prompt": "Child?"},
            ],
        },
    )


def _parent_wizard_flow() -> FlowDefinition:
    return FlowDefinition(
        id="flow-parent-wizard-554",
        name="parent-wizard-554",
        pattern="wizard",
        options={
            "steps": [
                {
                    "slug": "spawn_child",
                    "title": "Spawn",
                    "step_kind": "resource",
                    "resource_ref": "submit-child-554",
                    "output_key": "child_job",
                },
            ],
        },
    )


def _submit_child_resource() -> ResourceDefinition:
    return ResourceDefinition(
        id="resource-submit-child-554",
        name="submit-child-554",
        provider="palm",
        action="submit_flow",
        resource_id="flow:child-wizard-554",
        params={
            "wait": True,
            "wait_mode": "until_input",
            "timeout_seconds": 5,
        },
    )


def _seed(runtime: EmbeddedRuntime) -> None:
    runtime.repository.save_flow(_child_wizard_flow())
    runtime.repository.save_flow(_parent_wizard_flow())
    runtime.repository.save_resource(_submit_child_resource())


@pytest.fixture
def runtime() -> EmbeddedRuntime:
    rt = EmbeddedRuntime()
    rt.start()
    _seed(rt)
    yield rt
    rt.stop()
    clear_palm_runtime()


def test_runtime_wires_wait_matcher(runtime: EmbeddedRuntime) -> None:
    assert runtime.wait_matcher is not None


def test_nested_unpark_via_matcher_only(runtime: EmbeddedRuntime) -> None:
    """Wait interest + matcher alone completes nested flow (no completion hook)."""
    parent_job = runtime.submit_flow("parent-wizard-554")
    runtime.wait_until_idle(timeout=5)

    assert parent_job.status == JobStatus.WAITING_FOR_INPUT
    from plugins.patterns.wizard.bindings.resource.nested_park import nested_park_interest

    park = nested_park_interest(parent_job.state)
    assert park is not None
    child_job_id = park.target_id
    assert has_open_waits(parent_job.state)
    interests = list_wait_interests(parent_job.state)
    assert interests[0].target_id == str(child_job_id)

    runtime.provide_input(child_job_id, "answer")
    runtime.wait_until_idle(timeout=5)

    child_job = runtime.get_job(str(child_job_id))
    assert child_job.status == JobStatus.SUCCEEDED

    parent_job = runtime.get_job(parent_job.id)
    assert parent_job.status == JobStatus.SUCCEEDED
    answers = parent_job.state.get(WizardKeys.ANSWERS) or {}
    assert isinstance(answers.get("child_job"), dict)
    assert not has_open_waits(parent_job.state)
    assert nested_park_interest(parent_job.state) is None


def test_matcher_scan_discovers_owner_without_index() -> None:
    """list_jobs scan finds parents that only opened state interest (0.55.3)."""
    from palm.system.subsystems.planes.wait.index import WaitOwnerIndex
    from palm.system.subsystems.planes.wait.matcher import WaitMatcher
    from palm.core.orchestration import Job
    from palm.core.wait import make_job_wait, open_wait_on_job

    owner = Job(id="owner-scan", executable=None)
    owner.status = JobStatus.WAITING_FOR_INPUT
    open_wait_on_job(owner, make_job_wait("child-scan"))

    resumes: list[str] = []
    matcher = WaitMatcher(
        index=WaitOwnerIndex(),  # empty — force scan
        get_job={owner.id: owner}.get,
        list_jobs=lambda: [owner],
        resume_owner=lambda oid, _i, _s: resumes.append(oid),
    )
    disps = matcher.handle_payload(
        "job.completed",
        {"job_id": "child-scan", "status": "SUCCEEDED"},
    )
    assert len(disps) == 1
    assert resumes == ["owner-scan"]
    assert not has_open_waits(owner.state)
