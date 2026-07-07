"""Tests for flow_revision pins on submit (0.24.1)."""

from __future__ import annotations

from palm.common.executions.flow_submission import prepare_flow_submission
from palm.common.persistence.instance_sync import build_instance_from_job
from palm.common.persistence.definition_repository import DefinitionRepository
from palm.common.patterns import PatternBuildContext
from palm.core.orchestration import Job, JobStatus
from palm.definitions import FlowDefinition
from palm.states import BlackboardState


def test_prepare_flow_submission_sets_flow_revision_metadata() -> None:
    repo = DefinitionRepository()
    flow = repo.publish_flow_revision(
        FlowDefinition(name="onboard", pattern="wizard", options={"step_count": 1}),
    )
    submission = prepare_flow_submission(
        flow,
        state=None,
        metadata=None,
        instances=None,
        build_ctx=PatternBuildContext(definition_repository=repo),
        instance_id="inst-1",
    )
    assert submission.metadata["flow_revision"] == flow.revision
    assert submission.metadata["flow_definition"]["revision"] == flow.revision


def test_build_instance_from_job_pins_flow_revision() -> None:
    repo = DefinitionRepository()
    flow = repo.publish_flow_revision(
        FlowDefinition(name="onboard", pattern="wizard", options={"step_count": 1}),
    )
    repo.publish_flow_revision(
        FlowDefinition(
            name="onboard",
            pattern="wizard",
            options={"steps": [{"slug": "v2", "title": "V2", "prompt": "?"}]},
        ),
    )
    job = Job(
        id="job-1",
        executable=object(),
        state=BlackboardState(),
        metadata={"pattern": "wizard", "flow_revision": flow.revision},
        status=JobStatus.WAITING_FOR_INPUT,
    )
    instance = build_instance_from_job(job, flow=flow, instance_id="inst-1")
    assert instance.flow_revision == 1
    assert instance.flow_definition["revision"] == 1


def test_legacy_instance_without_flow_revision_still_roundtrips() -> None:
    from palm.instances import ProcessInstance

    instance = ProcessInstance(
        instance_id="inst-legacy",
        job_id="job-1",
        status="WAITING_FOR_INPUT",
        state_snapshot={},
        flow_definition={"name": "onboard", "pattern": "wizard", "options": {}},
        pattern="wizard",
    )
    restored = ProcessInstance.from_dict(instance.to_dict())
    assert restored.flow_revision is None