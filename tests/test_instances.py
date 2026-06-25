"""Tests for durable process instances and resume."""

from __future__ import annotations

import pytest

from palm.common import InstanceNotFoundError, InstanceRepository, InstanceResumeError
from palm.core import StorageEngine
from palm.core.orchestration import JobStatus
from palm.definitions import FlowDefinition
from palm.instances import ProcessInstance
from palm.patterns.wizard import WizardKeys
from palm.patterns.wizard.bindings.definitions.config import WizardConfig
from palm.runtimes.embedded import EmbeddedRuntime
from palm.storages import memory  # noqa: F401


def _wizard_flow() -> FlowDefinition:
    return FlowDefinition(
        name="onboard",
        pattern="wizard",
        options={
            "steps": [
                {"slug": "name", "title": "Name", "prompt": "Name?"},
                {
                    "slug": "role",
                    "title": "Role",
                    "prompt": "Role?",
                    "field_type": "choice",
                    "choices": ["dev", "mgr"],
                },
            ],
        },
    )


def test_process_instance_roundtrip_dict() -> None:
    inst = ProcessInstance(
        instance_id="inst-1",
        job_id="job-1",
        status="WAITING_FOR_INPUT",
        state_snapshot={"__wizard__.answers": {"name": "Ada"}},
        flow_definition=_wizard_flow().to_dict(),
        pattern="wizard",
        wizard_step_slug="role",
    )
    inst.append_status("PENDING", event="created")
    restored = ProcessInstance.from_dict(inst.to_dict())
    assert restored.instance_id == "inst-1"
    assert restored.state_snapshot["__wizard__.answers"]["name"] == "Ada"
    assert len(restored.status_history) == 1


def test_instance_repository_persistence_roundtrip() -> None:
    storage = StorageEngine()
    storage.initialize(backend="memory")
    repo = InstanceRepository(storage)

    inst = ProcessInstance(
        instance_id="inst-abc",
        job_id="job-abc",
        status=JobStatus.WAITING_FOR_INPUT.value,
        state_snapshot={"k": 1},
        flow_definition={"name": "f", "pattern": "wizard", "options": {}},
        pattern="wizard",
    )
    repo.save(inst)

    fresh = InstanceRepository(storage)
    loaded = fresh.get("inst-abc")
    assert loaded.job_id == "job-abc"
    assert loaded.state_snapshot["k"] == 1
    storage.shutdown()


def test_wizard_resume_after_runtime_restart() -> None:
    storage = StorageEngine()
    storage.initialize(backend="memory")

    rt1 = EmbeddedRuntime(storage=storage)
    rt1.start()
    job = rt1.submit_flow(_wizard_flow())
    instance_id = job.metadata["instance_id"]
    assert job.status == JobStatus.WAITING_FOR_INPUT

    rt1.provide_input(job.id, "Ada")
    assert job.status == JobStatus.WAITING_FOR_INPUT
    assert rt1.current_wizard_step(job.id) == "role"
    rt1.executor.persist_job(job)
    rt1.stop()

    rt2 = EmbeddedRuntime(storage=storage)
    rt2.start()
    try:
        resumed_job = rt2.resume_process(instance_id)
        assert resumed_job.metadata["resumed"] is True
        assert resumed_job.status == JobStatus.WAITING_FOR_INPUT
        assert rt2.current_wizard_step(resumed_job.id) == "role"
        assert resumed_job.state.get(WizardKeys.ANSWERS)["name"] == "Ada"

        rt2.provide_input(resumed_job.id, "dev")
        assert resumed_job.status == JobStatus.SUCCEEDED
        assert rt2.wizard_answers(resumed_job.id)["role"] == "dev"
    finally:
        rt2.stop()
        storage.shutdown()


def test_resume_terminal_instance_raises() -> None:
    storage = StorageEngine()
    storage.initialize(backend="memory")
    rt = EmbeddedRuntime(storage=storage)
    rt.start()
    try:
        job = rt.submit_wizard(
            config=WizardConfig.from_slugs(["only"]),
        )
        instance_id = job.metadata["instance_id"]
        rt.provide_input(job.id, "done")
        assert job.status == JobStatus.SUCCEEDED
        rt.executor.persist_job(job)

        with pytest.raises(InstanceResumeError, match="not resumable"):
            rt.resume_process(instance_id)
    finally:
        rt.stop()
        storage.shutdown()


def test_get_instance_not_found() -> None:
    storage = StorageEngine()
    storage.initialize(backend="memory")
    rt = EmbeddedRuntime(storage=storage)
    rt.start()
    try:
        with pytest.raises(InstanceNotFoundError):
            rt.get_instance("missing")
    finally:
        rt.stop()
        storage.shutdown()
