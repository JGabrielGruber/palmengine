"""Phase 4 CQRS tests — projections, backtracking, CLI queries."""

from __future__ import annotations

from palm.app import ApplicationHost, HostProfile, PalmSettings
from palm.common.cqrs.query import ListInstancesQuery
from palm.core.event import Event, EventContext, EventEngine
from palm.core.orchestration.events import OrchestrationEventType
from palm.core.storage import StorageEngine
from palm.patterns.wizard import WizardConfig, WizardEventType, WizardPattern, WizardStepConfig
from palm.patterns.wizard.bindings.cqrs.projection import WizardProgressProjection
from palm.patterns.wizard.bindings.cqrs.queries import GetWizardProgressQuery
from palm.patterns.wizard.bindings.events.types import WizardEventType as WizardEvents
from palm.runtimes.cli.shared.args import CliInvocation
from palm.runtimes.cli.shared.bootstrap import bootstrap_runtime
from palm.states import BlackboardState


def _storage() -> StorageEngine:
    engine = StorageEngine()
    engine.initialize()
    engine.select("memory")
    return engine


def test_wizard_progress_records_backtrack_trace() -> None:
    storage = _storage()
    projection = WizardProgressProjection(storage)
    ctx = EventContext(job_id="job-1", instance_id="inst-1")

    projection.apply(
        Event(
            type=WizardEvents.BACKTRACK_REQUESTED,
            payload={"from_step": "role", "to_slug": "name"},
            context=ctx,
        )
    )
    projection.apply(
        Event(
            type=WizardEvents.BACKTRACK_EXECUTED,
            payload={"from_step": "role", "to_slug": "name", "slug": "name"},
            context=ctx,
        )
    )

    progress = projection.get_progress(GetWizardProgressQuery(instance_id="inst-1"))
    assert progress is not None
    assert progress.current_step == "name"
    assert len(progress.backtrack_trace) == 2
    assert progress.backtrack_trace[0].event_type == WizardEvents.BACKTRACK_REQUESTED
    assert progress.backtrack_trace[1].to_step == "name"
    storage.shutdown()


def test_wizard_live_events_update_progress_projection() -> None:
    from palm.core.context import ContextEngine

    storage = _storage()
    engine = EventEngine()
    engine.initialize()
    projection = WizardProgressProjection(storage)
    engine.subscribe(
        "*", lambda event: projection.apply(event) if projection.handles(event.type) else None
    )

    config = WizardConfig(
        steps=(
            WizardStepConfig(slug="name", title="Name", prompt="Name?"),
            WizardStepConfig(
                slug="role", title="Role", prompt="Role?", field_type="choice", choices=("dev",)
            ),
            WizardStepConfig(slug="confirm", title="Confirm", prompt="Ok?", field_type="confirm"),
        ),
        allow_backtrack=True,
    )
    state = BlackboardState()
    ctx = ContextEngine()
    ctx.initialize()
    ctx.push("job:job-1", state=state, job_id="job-1", instance_id="inst-1")
    wizard = WizardPattern(
        name="demo",
        config=config,
        event_engine=engine,
        context_engine=ctx,
    )

    wizard.tick(state)
    wizard.provide_input(state, "Ada")
    wizard.tick(state)
    wizard.provide_input(state, "dev")
    wizard.tick(state)
    wizard.request_backtrack(state, "name")
    wizard.tick(state)

    progress = projection.get_progress(GetWizardProgressQuery(instance_id="inst-1"))
    assert progress is not None
    assert any(
        entry.event_type == WizardEvents.BACKTRACK_REQUESTED for entry in progress.backtrack_trace
    )
    ctx.shutdown()
    engine.shutdown()
    storage.shutdown()


def test_host_job_board_updates_on_submit(settings: PalmSettings) -> None:
    from palm.definitions.flow import FlowDefinition

    host = ApplicationHost(settings=settings, profile=HostProfile.all_in_one())
    host.start()

    flow = FlowDefinition(name="quick", pattern="dag", options={"name": "quick"})
    job = host.submit_flow(flow, job_id="board-1")
    views = host.list_job_views()
    assert any(row.job_id == job.id for row in views)

    host.shutdown()


def test_cli_context_uses_query_bus_for_instance_list(fast_cli_settings: PalmSettings) -> None:
    invocation = CliInvocation(command="doctor", output_format="json")
    ctx = bootstrap_runtime(
        invocation=invocation,
        settings=fast_cli_settings,
        show_banner=False,
    )
    try:
        summaries = ctx.list_instance_summaries()
        assert isinstance(summaries, list)
        queried = ctx.host.ask(ListInstancesQuery(include_terminal=True))
        assert len(summaries) == len(queried)
    finally:
        from palm.runtimes.cli.shared.bootstrap import shutdown_context

        shutdown_context(ctx)


def test_backtrack_executed_carries_from_and_to_slug() -> None:
    events: list[Event] = []
    engine = EventEngine()
    engine.initialize()
    engine.subscribe("*", lambda e: events.append(e))

    config = WizardConfig(
        steps=(
            WizardStepConfig(slug="name", title="Name", prompt="Name?"),
            WizardStepConfig(
                slug="role", title="Role", prompt="Role?", field_type="choice", choices=("dev",)
            ),
            WizardStepConfig(slug="confirm", title="Confirm", prompt="Ok?", field_type="confirm"),
        ),
        allow_backtrack=True,
    )
    state = BlackboardState()
    wizard = WizardPattern(name="demo", config=config, event_engine=engine)

    wizard.tick(state)
    wizard.provide_input(state, "Ada")
    wizard.tick(state)
    wizard.provide_input(state, "dev")
    wizard.tick(state)
    assert wizard.current_step_slug(state) == "confirm"
    wizard.request_backtrack(state, "name")
    wizard.tick(state)

    executed = [e for e in events if e.type == WizardEventType.BACKTRACK_EXECUTED]
    assert executed
    assert executed[-1].payload.get("from_step") == "confirm"
    assert executed[-1].payload.get("to_slug") == "name"
    requested = [e for e in events if e.type == WizardEventType.BACKTRACK_REQUESTED]
    assert requested
    assert requested[-1].payload.get("from_step") == "confirm"
    engine.shutdown()


def test_instance_index_updates_step_on_backtrack_event() -> None:
    from palm.common.cqrs.projections.instance_index import InstanceIndexProjection

    storage = _storage()

    class _Manager:
        def list_summaries(self):
            return []

        def get(self, instance_id: str):
            raise RuntimeError("not used")

    projection = InstanceIndexProjection(storage, _Manager())
    projection.apply(
        Event(
            type=OrchestrationEventType.INSTANCE_STATUS_CHANGED,
            payload={"instance_id": "inst-1", "job_id": "j-1", "status": "WAITING_FOR_INPUT"},
        )
    )
    projection.apply(
        Event(
            type="wizard.backtrack.executed",
            payload={"from_step": "role", "to_slug": "name"},
            context=EventContext(instance_id="inst-1", job_id="j-1"),
        )
    )
    from palm.common.cqrs.query import GetInstanceStatusQuery

    view = projection.get_instance(GetInstanceStatusQuery(instance_id="inst-1"))
    assert view is not None
    assert view.current_step_slug == "name"
    storage.shutdown()
