"""Tests for InstanceManager coordination layer."""

from __future__ import annotations

import pytest

from palm.app import PalmApp, PalmSettings
from palm.common import InstanceNotFoundError, InstanceRepository
from palm.common.exceptions import InstanceActiveLimitError
from palm.common.managers import InstanceManager, InstanceSummary
from palm.core import StorageEngine
from palm.core.orchestration import JobStatus
from palm.definitions import FlowDefinition
from palm.instances import ProcessInstance, StateSnapshot
from palm.runtimes.embedded import EmbeddedRuntime
from palm.storages import memory  # noqa: F401


def _wizard_flow() -> FlowDefinition:
    return FlowDefinition(
        name="onboard",
        pattern="wizard",
        options={"steps": [{"slug": "name", "title": "Name", "prompt": "Name?"}]},
    )


def _sample_instance(
    instance_id: str = "inst-1", *, status: str = "WAITING_FOR_INPUT"
) -> ProcessInstance:
    return ProcessInstance(
        instance_id=instance_id,
        job_id=f"job-{instance_id}",
        status=status,
        state_snapshot={"k": 1},
        flow_definition=_wizard_flow().to_dict(),
        pattern="wizard",
        flow_name="onboard",
    )


def test_instance_manager_lru_cache_and_lazy_load() -> None:
    storage = StorageEngine()
    storage.initialize(backend="memory")
    repo = InstanceRepository(storage)
    manager = InstanceManager(repo, settings=PalmSettings(max_loaded_instances=2))
    manager.initialize(reconcile_on_startup=False)

    for index in range(3):
        manager.save(_sample_instance(f"inst-{index}"))

    assert manager.get("inst-0").instance_id == "inst-0"
    assert manager.get("inst-2").instance_id == "inst-2"
    # inst-1 was LRU-evicted from cache but still loadable
    assert manager.get("inst-1").instance_id == "inst-1"

    manager.shutdown()
    storage.shutdown()


def test_active_instances_are_not_evicted() -> None:
    storage = StorageEngine()
    storage.initialize(backend="memory")
    repo = InstanceRepository(storage)
    manager = InstanceManager(
        repo,
        settings=PalmSettings(max_loaded_instances=1, max_concurrent_active=2),
    )
    manager.initialize(reconcile_on_startup=False)

    manager.save(_sample_instance("inst-a"))
    manager.save(_sample_instance("inst-b"))
    manager.mark_active("inst-a")
    manager.get("inst-b")

    assert "inst-a" in manager.active_instance_ids
    assert manager.get("inst-a").instance_id == "inst-a"

    manager.shutdown()
    storage.shutdown()


def test_acquire_does_not_leak_active_slot_on_missing_instance() -> None:
    storage = StorageEngine()
    storage.initialize(backend="memory")
    repo = InstanceRepository(storage)
    manager = InstanceManager(
        repo,
        settings=PalmSettings(max_concurrent_active=1),
    )
    manager.initialize(reconcile_on_startup=False)

    with pytest.raises(InstanceNotFoundError):
        manager.acquire("inst-missing")

    assert manager.active_instance_ids == set()
    manager.mark_active("inst-other")
    manager.shutdown()
    storage.shutdown()


def test_acquire_marks_active_after_successful_load() -> None:
    storage = StorageEngine()
    storage.initialize(backend="memory")
    repo = InstanceRepository(storage)
    manager = InstanceManager(repo)
    manager.initialize(reconcile_on_startup=False)
    manager.save(_sample_instance("inst-acquire"))

    loaded = manager.acquire("inst-acquire")
    assert loaded.instance_id == "inst-acquire"
    assert "inst-acquire" in manager.active_instance_ids

    manager.shutdown()
    storage.shutdown()


def test_active_limit_enforced() -> None:
    storage = StorageEngine()
    storage.initialize(backend="memory")
    repo = InstanceRepository(storage)
    manager = InstanceManager(
        repo,
        settings=PalmSettings(max_concurrent_active=1),
    )
    manager.initialize(reconcile_on_startup=False)
    manager.save(_sample_instance("inst-a"))

    manager.mark_active("inst-a")
    with pytest.raises(InstanceActiveLimitError):
        manager.mark_active("inst-b")

    manager.shutdown()
    storage.shutdown()


def test_list_summaries_without_full_load() -> None:
    storage = StorageEngine()
    storage.initialize(backend="memory")
    repo = InstanceRepository(storage)
    manager = InstanceManager(repo)
    manager.initialize(reconcile_on_startup=False)

    inst = _sample_instance("inst-sum")
    inst.state_snapshots.append(
        StateSnapshot(
            status="WAITING_FOR_INPUT",
            state_snapshot={"x": 1},
            job_id="job-inst-sum",
            recorded_at="2026-06-10T12:00:00+00:00",
        )
    )
    manager.save(inst)

    summaries = manager.list_summaries()
    assert len(summaries) == 1
    summary = summaries[0]
    assert isinstance(summary, InstanceSummary)
    assert summary.instance_id == "inst-sum"
    assert summary.flow_name == "onboard"
    assert summary.snapshot_count == 1

    manager.shutdown()
    storage.shutdown()


def test_reconcile_marks_stale_running_and_removes_orphans() -> None:
    storage = StorageEngine()
    storage.initialize(backend="memory")
    repo = InstanceRepository(storage)

    stale = _sample_instance("inst-stale", status=JobStatus.RUNNING.value)
    repo.save(stale)
    repo.purge_index_entry("inst-orphan")
    storage.set("palm:instances:index", ["inst-stale", "inst-orphan"])

    manager = InstanceManager(repo)
    report = manager.reconcile()

    assert "inst-stale" in report.stale_marked
    assert "inst-orphan" in report.orphans_removed

    restored = manager.get("inst-stale")
    assert restored.status == JobStatus.WAITING_FOR_INPUT.value
    assert restored.status_history[-1].detail.get("event") == "reconciled_stale"

    with pytest.raises(InstanceNotFoundError):
        manager.get("inst-orphan")

    storage.shutdown()


def test_instance_manager_integrates_with_embedded_runtime() -> None:
    storage = StorageEngine()
    storage.initialize(backend="memory")

    rt = EmbeddedRuntime(storage=storage)
    rt.start(reconcile_on_startup=False)
    try:
        job = rt.submit_flow(_wizard_flow())
        instance_id = job.metadata["instance_id"]
        assert instance_id in rt.instance_manager.active_instance_ids

        loaded = rt.get_instance(instance_id)
        assert loaded.flow_name == "onboard"
        assert rt.instance_manager.get(instance_id) is loaded
    finally:
        rt.stop()
        storage.shutdown()


def test_palm_app_exposes_shared_instance_manager(tmp_path) -> None:
    settings = PalmSettings(
        storage_backend="memory",
        max_loaded_instances=64,
        reconcile_instances_on_startup=False,
    )
    with PalmApp(settings) as app:
        app.create_runtime("embedded", autostart=True)
        inst = ProcessInstance(
            instance_id="inst-app",
            job_id="job-app",
            status="PENDING",
            state_snapshot={},
            flow_definition=_wizard_flow().to_dict(),
            pattern="wizard",
            flow_name="onboard",
        )
        app.instance_manager.save(inst)

        summary = app.list_instance_summaries()[0]
        assert summary.instance_id == "inst-app"
        assert app.get_instance("inst-app").job_id == "job-app"
        assert app.instance_manager is app.runtime().instance_manager


def test_list_instances_skips_corrupt_records() -> None:
    storage = StorageEngine()
    storage.initialize(backend="memory")
    repo = InstanceRepository(storage)
    manager = InstanceManager(repo)
    manager.initialize(reconcile_on_startup=False)

    manager.save(_sample_instance("inst-good"))
    storage.set("palm:instances:index", ["inst-good", "inst-bad"])
    storage.set("palm:instances:inst-bad", "not-a-dict")

    instances = manager.list_instances()
    assert [item.instance_id for item in instances] == ["inst-good"]

    manager.shutdown()
    storage.shutdown()
