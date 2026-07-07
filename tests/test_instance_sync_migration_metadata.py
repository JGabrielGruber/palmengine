"""Tests that job sync preserves instance migration metadata (0.24.3)."""

from __future__ import annotations

from palm.common.persistence.instance_sync import build_instance_from_job, update_instance_from_job
from palm.core.orchestration import Job, JobStatus
from palm.definitions import FlowDefinition
from palm.states import BlackboardState


def test_update_instance_from_job_preserves_migration_metadata() -> None:
    flow = FlowDefinition(name="onboard", pattern="wizard", options={"steps": 1})
    state = BlackboardState()
    job = Job(
        id="job-1",
        executable=object(),
        state=state,
        metadata={
            "instance_id": "inst-1",
            "pattern": "wizard",
            "operator": "agent",
        },
        status=JobStatus.RUNNING,
    )
    instance = build_instance_from_job(job, flow=flow, instance_id="inst-1")
    instance.metadata["migration_status"] = "failed"
    instance.metadata["migration_target_revision"] = 4
    instance.metadata["migration_from_revision"] = 3
    instance.metadata["migration_blockers"] = ["blocked field"]

    job.metadata["operator"] = "human"
    update_instance_from_job(instance, job)

    assert instance.metadata["operator"] == "human"
    assert instance.metadata["migration_status"] == "failed"
    assert instance.metadata["migration_target_revision"] == 4
    assert instance.metadata["migration_from_revision"] == 3
    assert instance.metadata["migration_blockers"] == ["blocked field"]