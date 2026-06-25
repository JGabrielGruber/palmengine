"""Tests for optional state snapshot middleware."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from palm.app import PalmApp, PalmSettings
from palm.common.hooks.state_snapshot import StateSnapshotHook
from palm.common.persistence.instance_repository import InstanceRepository
from palm.core import StorageEngine
from palm.core.orchestration import Job, JobStatus, OrchestrationEngine
from palm.definitions import FlowDefinition
from palm.instances import ProcessInstance, StateSnapshot
from palm.patterns.wizard import WizardKeys
from palm.runtimes.embedded import EmbeddedRuntime
from palm.storages import memory  # noqa: F401


def _wizard_flow() -> FlowDefinition:
    return FlowDefinition(
        name="snap-wizard",
        pattern="wizard",
        options={
            "steps": [
                {"slug": "alpha", "title": "Alpha", "prompt": "Alpha?"},
                {"slug": "beta", "title": "Beta", "prompt": "Beta?"},
            ],
        },
    )


def test_state_snapshot_roundtrip_dict() -> None:
    snapshot = StateSnapshot(
        status="WAITING_FOR_INPUT",
        recorded_at="2026-01-01T00:00:00+00:00",
        state_snapshot={"answers": {"alpha": "one"}},
        job_id="job-1",
        current_step_slug="beta",
    )
    restored = StateSnapshot.from_dict(snapshot.to_dict())
    assert restored.status == "WAITING_FOR_INPUT"
    assert restored.state_snapshot["answers"]["alpha"] == "one"


def test_process_instance_persists_state_snapshots() -> None:
    storage = StorageEngine()
    storage.initialize(backend="memory")
    repo = InstanceRepository(storage)

    inst = ProcessInstance(
        instance_id="inst-snap",
        job_id="job-snap",
        status=JobStatus.WAITING_FOR_INPUT.value,
        state_snapshot={"k": 1},
        flow_definition=_wizard_flow().to_dict(),
        pattern="wizard",
    )
    inst.append_state_snapshot(
        StateSnapshot(
            status="WAITING_FOR_INPUT",
            recorded_at="2026-01-01T00:00:00+00:00",
            state_snapshot={"k": 1},
            job_id="job-snap",
        )
    )
    repo.save(inst)

    loaded = InstanceRepository(storage).get("inst-snap")
    assert len(loaded.state_snapshots) == 1
    assert loaded.state_snapshots[0].status == "WAITING_FOR_INPUT"
    storage.shutdown()


def test_state_snapshot_hook_records_configured_statuses() -> None:
    storage = StorageEngine()
    storage.initialize(backend="memory")
    repo = InstanceRepository(storage)
    hook = StateSnapshotHook(
        repo,
        snapshot_on_status=["WAITING_FOR_INPUT", "SUCCEEDED"],
        max_snapshots_per_instance=5,
    )

    engine = OrchestrationEngine()
    engine.initialize(
        scheduler=MagicMock(),
        hooks=[hook],
    )
    engine.start()

    job = Job(id="job-hook", executable={"noop": True}, metadata={"instance_id": "inst-hook"})
    job.status = JobStatus.WAITING_FOR_INPUT
    repo.save(
        ProcessInstance(
            instance_id="inst-hook",
            job_id="job-hook",
            status=JobStatus.WAITING_FOR_INPUT.value,
            state_snapshot={},
            flow_definition=_wizard_flow().to_dict(),
            pattern="wizard",
        )
    )

    hook.on_job_status_changed(engine, job)
    hook.on_job_status_changed(engine, job)

    snapshots = repo.list_state_snapshots("inst-hook")
    assert len(snapshots) == 2
    assert all(item.status == "WAITING_FOR_INPUT" for item in snapshots)

    job.status = JobStatus.SUCCEEDED
    hook.on_job_status_changed(engine, job)
    snapshots = repo.list_state_snapshots("inst-hook")
    assert len(snapshots) == 3
    assert snapshots[-1].status == "SUCCEEDED"
    engine.shutdown()
    storage.shutdown()


def test_state_snapshot_hook_trims_to_max() -> None:
    storage = StorageEngine()
    storage.initialize(backend="memory")
    repo = InstanceRepository(storage)
    hook = StateSnapshotHook(
        repo, snapshot_on_status=["WAITING_FOR_INPUT"], max_snapshots_per_instance=2
    )

    engine = OrchestrationEngine()
    engine.initialize(scheduler=MagicMock(), hooks=[hook])
    engine.start()

    job = Job(id="job-trim", executable={}, metadata={"instance_id": "inst-trim"})
    job.status = JobStatus.WAITING_FOR_INPUT
    repo.save(
        ProcessInstance(
            instance_id="inst-trim",
            job_id="job-trim",
            status=JobStatus.WAITING_FOR_INPUT.value,
            state_snapshot={},
            flow_definition=_wizard_flow().to_dict(),
            pattern="wizard",
        )
    )

    for _ in range(4):
        hook.on_job_status_changed(engine, job)

    snapshots = repo.list_state_snapshots("inst-trim")
    assert len(snapshots) == 2
    engine.shutdown()
    storage.shutdown()


def test_state_snapshot_hook_swallows_repository_errors() -> None:
    class _FailingRepo:
        def get(self, instance_id: str) -> ProcessInstance:
            raise RuntimeError("storage unavailable")

        def append_state_snapshot(self, *args, **kwargs) -> None:
            raise RuntimeError("should not be called")

    hook = StateSnapshotHook(_FailingRepo(), snapshot_on_status=["SUCCEEDED"])
    job = Job(id="job-fail", executable={}, metadata={"instance_id": "inst-fail"})
    job.status = JobStatus.SUCCEEDED
    hook.on_job_status_changed(OrchestrationEngine(), job)


def test_embedded_runtime_snapshots_wizard_flow_when_enabled() -> None:
    storage = StorageEngine()
    storage.initialize(backend="memory")
    rt = EmbeddedRuntime(storage=storage)
    rt.start(
        enable_state_snapshot=True,
        snapshot_on_status=["WAITING_FOR_INPUT", "SUCCEEDED"],
        max_snapshots_per_instance=10,
    )
    try:
        job = rt.submit_flow(_wizard_flow())
        instance_id = job.metadata["instance_id"]
        assert job.status == JobStatus.WAITING_FOR_INPUT

        snapshots = rt.instances.list_state_snapshots(instance_id)
        assert len(snapshots) == 1
        assert snapshots[0].status == "WAITING_FOR_INPUT"
        assert snapshots[0].current_step_slug == "alpha"

        rt.provide_input(job.id, "first")
        assert job.status == JobStatus.WAITING_FOR_INPUT
        snapshots = rt.instances.list_state_snapshots(instance_id)
        assert len(snapshots) == 2
        assert snapshots[-1].current_step_slug == "beta"
        assert snapshots[-1].state_snapshot.get(WizardKeys.ANSWERS, {}).get("alpha") == "first"

        rt.provide_input(job.id, "second")
        assert job.status == JobStatus.SUCCEEDED
        snapshots = rt.instances.list_state_snapshots(instance_id)
        assert len(snapshots) == 3
        assert snapshots[-1].status == "SUCCEEDED"
    finally:
        rt.stop()
        storage.shutdown()


def test_palm_app_wires_snapshot_settings(app: PalmApp) -> None:
    app.settings = PalmSettings(
        load_example_definitions=False,
        enable_state_snapshot=True,
        snapshot_on_status=["SUCCEEDED"],
        max_snapshots_per_instance=3,
    )
    runtime = app.create_runtime("embedded", autostart=True)
    assert any(isinstance(hook, StateSnapshotHook) for hook in runtime.orchestration._hooks)


@pytest.fixture
def app() -> PalmApp:
    application = PalmApp(PalmSettings(load_example_definitions=False))
    application.bootstrap()
    return application
