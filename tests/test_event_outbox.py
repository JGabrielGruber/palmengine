"""Tests for reliable outbox publishing."""

from __future__ import annotations

from palm.common.events import (
    DomainEventType,
    OutboxProcessor,
    OutboxStore,
    wire_reliable_events,
)
from palm.common.hooks import InstancePersistenceHook
from palm.core.event import Event, EventContext, EventEngine
from palm.core.orchestration import Job, OrchestrationEngine
from palm.core.orchestration.events import OrchestrationEventType
from palm.core.storage import StorageEngine
from palm.definitions.flow import FlowDefinition
from palm.patterns.wizard import WizardConfig, WizardPattern, WizardStepConfig
from palm.patterns.wizard.bindings.events.types import WizardEventType
from palm.states import BlackboardState
from tests.core.fakes import TestState
from tests.core.fakes.mode import TestMode


def _memory_storage() -> StorageEngine:
    storage = StorageEngine()
    storage.initialize()
    storage.select("memory")
    return storage


def test_outbox_interceptor_records_critical_live_events() -> None:
    storage = _memory_storage()
    store = OutboxStore(storage)
    engine = EventEngine()
    engine.initialize()
    wire_reliable_events(engine, store)

    engine.emit(
        WizardEventType.STEP_COMPLETED,
        context=EventContext(job_id="j-1", instance_id="i-1"),
        slug="name",
    )

    pending = store.list_pending()
    assert len(pending) == 1
    assert pending[0].event_type == WizardEventType.STEP_COMPLETED
    assert pending[0].context is not None
    assert pending[0].context["job_id"] == "j-1"
    engine.shutdown()
    storage.shutdown()


def test_outbox_processor_marks_entries_published() -> None:
    storage = _memory_storage()
    store = OutboxStore(storage)
    engine = EventEngine()
    engine.initialize()
    processor = OutboxProcessor(store, engine)

    store.enqueue(
        Event(
            type="job.completed",
            payload={"job_id": "j-1"},
            context=EventContext(job_id="j-1"),
        )
    )
    assert store.pending_count() == 1

    processed = processor.process_batch()
    assert processed == 1
    assert store.pending_count() == 0
    engine.shutdown()
    storage.shutdown()


def test_instance_persistence_hook_enqueues_after_successful_write() -> None:
    storage = _memory_storage()
    store = OutboxStore(storage)

    class _Repo:
        def __init__(self) -> None:
            self._items: dict[str, object] = {}

        def get(self, instance_id: str) -> object:
            if instance_id not in self._items:
                from palm.common.exceptions import InstanceNotFoundError

                raise InstanceNotFoundError(instance_id)
            return self._items[instance_id]

        def create(self, job: Job, **kwargs: object) -> object:
            self._items[str(kwargs["instance_id"])] = {"job": job.id}
            return self._items[str(kwargs["instance_id"])]

        def update(self, job: Job, *, instance_id: str) -> object:
            self._items[instance_id] = {"job": job.id}
            return self._items[instance_id]

    repo = _Repo()
    hook = InstancePersistenceHook(repo, outbox_store=store)
    flow = FlowDefinition(name="demo", pattern="wizard")
    job = Job(
        id="job-abc",
        executable={"steps": 1},
        metadata={
            "instance_id": "inst-42",
            "flow_definition": flow.to_dict(),
        },
    )

    engine = OrchestrationEngine()
    hook.on_job_submitted(engine, job)

    pending = store.list_pending()
    assert len(pending) == 1
    assert pending[0].event_type == DomainEventType.INSTANCE_CREATED
    storage.shutdown()


def test_orchestration_emits_instance_status_with_context() -> None:
    events: list[tuple[str, dict]] = []
    event_engine = EventEngine()
    event_engine.initialize()
    event_engine.subscribe("*", lambda e: events.append((e.type, e.enriched_payload())))

    mode = TestMode()
    mode.start()
    orch = OrchestrationEngine()
    orch.initialize(scheduler=mode, event_engine=event_engine)
    orch.start()

    state = TestState()
    job = orch.submit(
        {"steps": 1, "final_status": "SUCCEEDED"},
        state=state,
        metadata={"instance_id": "inst-99", "trace_id": "trace-1"},
    )
    orch.stop()
    orch.shutdown()
    event_engine.shutdown()

    types = [item[0] for item in events]
    assert OrchestrationEventType.INSTANCE_STATUS_CHANGED in types
    instance_events = [
        payload for t, payload in events if t == OrchestrationEventType.INSTANCE_STATUS_CHANGED
    ]
    assert instance_events[-1]["instance_id"] == "inst-99"
    assert instance_events[-1]["job_id"] == job.id
    assert instance_events[-1]["trace_id"] == "trace-1"


def test_wizard_emits_step_completed_and_backtrack_executed() -> None:
    events: list[str] = []
    engine = EventEngine()
    engine.initialize()
    engine.subscribe("*", lambda e: events.append(e.type))

    config = WizardConfig(
        steps=(
            WizardStepConfig(slug="name", title="Name", prompt="Name?"),
            WizardStepConfig(slug="role", title="Role", prompt="Role?"),
        ),
        allow_backtrack=True,
    )
    state = BlackboardState()
    wizard = WizardPattern(name="demo", config=config, event_engine=engine)

    wizard.tick(state)
    wizard.provide_input(state, "Ada")
    wizard.tick(state)

    assert WizardEventType.STEP_COMPLETED in events

    wizard.request_backtrack(state, "name")
    wizard.tick(state)
    assert WizardEventType.BACKTRACK_EXECUTED in events
    engine.shutdown()
