"""Tests for Phase 5 — compensation, webhooks, projection rebuild safeguards."""

from __future__ import annotations

import pytest

from palm.app import ApplicationHost, HostProfile, PalmSettings
from palm.app.host.events import HostEventType
from palm.common.compensation import (
    CompensationCoordinator,
    CompensationEventType,
    CompensationResult,
    CompensationTrigger,
)
from palm.common.cqrs.projections.instance_index import InstanceIndexProjection, InstanceReadModel
from palm.common.compensation.registry import CompensationRegistry
from palm.common.cqrs.projections.wizard_progress import WizardProgressProjection
from palm.common.cqrs.query import GetWizardProgressQuery
from palm.common.cqrs.rebuild import ProjectionRebuildPolicy
from palm.common.events import OutboxStore, RecordingWebhookDeliverer, WebhookDispatcher, WebhookTarget

from palm.core.event import Event, EventContext, EventEngine
from palm.core.storage import StorageEngine


def _storage() -> StorageEngine:
    engine = StorageEngine()
    engine.initialize()
    engine.select("memory")
    return engine


class _Summary:
    def __init__(self, instance_id: str) -> None:
        self.instance_id = instance_id
        self.job_id = f"job-{instance_id}"
        self.status = "RUNNING"
        self.flow_name = "demo"
        self.process_name = None
        self.wizard_step_slug = None
        self.updated_at = "2026-06-01T00:00:00+00:00"
        self.snapshot_count = 0


class _FakeManager:
    def __init__(self, count: int) -> None:
        self._count = count

    def list_summaries(self):
        return [_Summary(f"inst-{index}") for index in range(self._count)]

    def get(self, instance_id: str):
        raise RuntimeError("not used")


def test_instance_projection_skips_fresh_rebuild() -> None:
    storage = _storage()
    manager = _FakeManager(2)
    projection = InstanceIndexProjection(storage, manager)
    projection._upsert(
        InstanceReadModel(
            instance_id="inst-0",
            job_id="job-inst-0",
            status="RUNNING",
            flow_name="demo",
            updated_at="2026-06-01T00:00:00+00:00",
        )
    )
    projection._upsert(
        InstanceReadModel(
            instance_id="inst-1",
            job_id="job-inst-1",
            status="RUNNING",
            flow_name="demo",
            updated_at="2026-06-01T00:00:00+00:00",
        )
    )

    count = projection.rebuild(policy=ProjectionRebuildPolicy(skip_if_fresh=True))
    assert count == 2
    assert projection.was_rebuild_skipped()
    storage.shutdown()


def test_instance_projection_batches_large_rebuild() -> None:
    storage = _storage()
    projection = InstanceIndexProjection(storage, _FakeManager(250))
    policy = ProjectionRebuildPolicy(batch_size=50, max_instances=100, skip_if_fresh=False)

    count = projection.rebuild(policy=policy)
    assert count == 250
    assert projection.used_batched_rebuild
    assert projection.rebuild_warnings
    storage.shutdown()


def test_wizard_progress_tracks_commit_failure() -> None:
    storage = _storage()
    projection = WizardProgressProjection(storage)
    engine = EventEngine()
    engine.initialize()
    projection.apply(
        Event(
            type=CompensationTrigger.COMMIT_FAILED,
            payload={"hook": "save_profile", "error": "disk full", "wizard": "onboard"},
            context=EventContext(job_id="job-1", instance_id="inst-1"),
        )
    )

    progress = projection.get_progress(GetWizardProgressQuery(instance_id="inst-1"))
    assert progress is not None
    assert progress.commit_status == "failed"
    assert progress.commit_hook == "save_profile"
    assert progress.commit_error == "disk full"
    storage.shutdown()


def test_compensation_runs_on_commit_failure() -> None:
    registry = CompensationRegistry()
    registry.register_for_commit_hook(
        "save_profile",
        lambda ctx: CompensationResult.success({"undone": ctx.error}),
    )
    engine = EventEngine()
    engine.initialize()
    coordinator = CompensationCoordinator(registry, engine)
    executed: list[str] = []
    engine.subscribe(CompensationEventType.EXECUTED, lambda e: executed.append(e.type))

    coordinator.attach(engine)
    event = Event(
        type=CompensationTrigger.COMMIT_FAILED,
        payload={"hook": "save_profile", "error": "disk full"},
        context=EventContext(job_id="job-1"),
    )
    results = coordinator.handle(event)

    assert len(results) == 1
    assert results[0].ok
    assert results[0].data == {"undone": "disk full"}
    assert CompensationEventType.EXECUTED in executed


def test_compensation_skipped_without_handler() -> None:
    registry = CompensationRegistry()
    engine = EventEngine()
    engine.initialize()
    coordinator = CompensationCoordinator(registry, engine)
    skipped: list[dict] = []
    engine.subscribe(
        CompensationEventType.SKIPPED,
        lambda e: skipped.append(dict(e.payload)),
    )

    coordinator.handle(
        Event(
            type=CompensationTrigger.COMMIT_FAILED,
            payload={"hook": "unknown_hook", "error": "boom"},
        )
    )

    assert skipped
    assert skipped[-1]["reason"] == "no_handler"


def test_webhook_dispatcher_records_delivery() -> None:
    deliverer = RecordingWebhookDeliverer()
    dispatcher = WebhookDispatcher(
        [WebhookTarget(url="https://example.test/hook", name="test")],
        deliverer=deliverer,
    )
    event = Event(type="wizard.commit.failed", payload={"error": "disk full"})

    deliveries = dispatcher.dispatch(event)

    assert len(deliveries) == 1
    assert deliveries[0].ok
    assert deliverer.deliveries[0]["url"] == "https://example.test/hook"
    assert deliverer.deliveries[0]["body"]["type"] == "wizard.commit.failed"


def test_outbox_processor_dispatches_webhooks_before_publish() -> None:
    from palm.common.events import OutboxProcessor

    storage = _storage()
    engine = EventEngine()
    engine.initialize()
    deliverer = RecordingWebhookDeliverer()
    dispatcher = WebhookDispatcher(
        [WebhookTarget(url="https://example.test/events")],
        deliverer=deliverer,
    )
    store = OutboxStore(storage)
    processor = OutboxProcessor(store, engine)
    store.enqueue(Event(type="job.completed", payload={"job_id": "j-1"}))

    processed = processor.process_batch(on_before_publish=dispatcher.dispatch)

    assert processed == 1
    assert len(deliverer.deliveries) == 1
    assert store.pending_count() == 0
    storage.shutdown()


@pytest.mark.integration
def test_host_recovery_includes_projection_report(full_recovery_settings: PalmSettings) -> None:
    recovered: list[dict] = []
    host = ApplicationHost(settings=full_recovery_settings, profile=HostProfile.all_in_one())
    host.event.subscribe(
        HostEventType.RECOVERED,
        lambda e: recovered.append(dict(e.payload)),
    )
    host.start()
    host.shutdown()

    assert recovered
    payload = recovered[-1]
    assert "projections" in payload
    projections = payload["projections"]
    assert "counts" in projections
    assert "instance_index" in projections["counts"]


def test_host_emits_workers_ready(settings: PalmSettings) -> None:
    events: list[str] = []
    profile = HostProfile(master=True, worker=True, server=False, worker_count=2)
    host = ApplicationHost(settings=settings, profile=profile)
    host.event.subscribe("*", lambda e: events.append(e.type))
    host.start()
    host.shutdown()

    assert HostEventType.WORKERS_READY in events


def test_commit_failure_event_is_critical() -> None:
    from palm.common.events import CRITICAL_EVENT_TYPES

    assert CompensationTrigger.COMMIT_FAILED in CRITICAL_EVENT_TYPES