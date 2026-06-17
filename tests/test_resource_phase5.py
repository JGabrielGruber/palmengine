"""Phase 5 integration — compensation, projections, correlation, enrich_resource."""

from __future__ import annotations

import pytest

from palm.common import DefinitionRepository
from palm.common.compensation import (
    CompensationCoordinator,
    CompensationEventType,
    CompensationResult,
    CompensationTrigger,
)
from palm.common.compensation.registry import CompensationRegistry
from palm.common.cqrs.projections.resource_invocation import ResourceInvocationProjection
from palm.common.cqrs.query import GetResourceInvocationsQuery
from palm.common.resource import resource_definition_resolver
from palm.common.resource.compensation import (
    is_mutating_action,
    resource_refs_for_compensation,
    track_resource_invocation,
)
from palm.common.resource.observability import stamp_execution_context
from palm.common.transforms import TransformExecutor, autoload
from palm.core.event import Event, EventContext, EventEngine
from palm.core.resource import ResourceEngine
from palm.core.resource.observability import resource_correlation
from palm.core.storage import StorageEngine
from palm.core.transform.registry import transform_registry
from palm.definitions import ResourceDefinition
from palm.states import BlackboardState


def _storage() -> StorageEngine:
    engine = StorageEngine()
    engine.initialize()
    engine.select("memory")
    return engine


def test_register_for_resource_runs_on_resource_failed() -> None:
    registry = CompensationRegistry()
    registry.register_for_resource(
        "submit-ingest-etl",
        lambda ctx: CompensationResult.success({"undone": ctx.resource_ref}),
    )
    bus = EventEngine()
    bus.initialize()
    coordinator = CompensationCoordinator(registry, bus)
    executed: list[str] = []
    bus.subscribe(CompensationEventType.EXECUTED, lambda e: executed.append(e.type))

    coordinator.handle(
        Event(
            type=CompensationTrigger.RESOURCE_FAILED,
            payload={
                "resource_ref": "submit-ingest-etl",
                "error": "timeout",
            },
            context=EventContext(job_id="job-1", instance_id="inst-1"),
        )
    )

    assert CompensationEventType.EXECUTED in executed


def test_commit_failure_compensates_tracked_resources() -> None:
    registry = CompensationRegistry()
    registry.register_for_resource(
        "mutate-customer",
        lambda ctx: CompensationResult.success({"rolled_back": True}),
    )
    bus = EventEngine()
    bus.initialize()
    coordinator = CompensationCoordinator(registry, bus)
    compensated: list[dict] = []
    bus.subscribe("resource.compensated", lambda e: compensated.append(dict(e.payload)))

    tracked = track_resource_invocation(
        [],
        resource_ref="mutate-customer",
        action="update",
        provider="rest",
        step_slug="apply",
    )
    coordinator.handle(
        Event(
            type=CompensationTrigger.COMMIT_FAILED,
            payload={
                "hook": "persist",
                "error": "disk full",
                "resource_refs": resource_refs_for_compensation(tracked),
                "resource_invocations": tracked,
            },
            context=EventContext(job_id="job-2"),
        )
    )

    assert compensated
    assert compensated[-1]["resource_ref"] == "mutate-customer"


def test_resource_invocation_projection_tracks_events() -> None:
    storage = _storage()
    projection = ResourceInvocationProjection(storage)
    projection.apply(
        Event(
            type="resource.invoked",
            payload={
                "provider": "rest",
                "action": "fetch",
                "resource_ref": "check-health",
                "step_slug": "preflight",
            },
            context=EventContext(job_id="job-3", instance_id="inst-3"),
        )
    )
    projection.apply(
        Event(
            type="resource.completed",
            payload={
                "provider": "rest",
                "action": "fetch",
                "resource_ref": "check-health",
                "step_slug": "preflight",
            },
            context=EventContext(job_id="job-3", instance_id="inst-3"),
        )
    )

    row = projection.get_invocations(GetResourceInvocationsQuery(instance_id="inst-3"))
    assert row is not None
    assert len(row.entries) == 2
    assert row.entries[0].event_type == "resource.invoked"
    assert row.entries[1].success is True
    storage.shutdown()


def test_resource_correlation_from_execution_stamp() -> None:
    state = BlackboardState()
    stamp_execution_context(
        state,
        job_id="job-9",
        instance_id="inst-9",
        flow="demo-flow",
        wizard="demo-wizard",
    )
    correlation = resource_correlation(state, step_slug="preflight")
    assert correlation["job_id"] == "job-9"
    assert correlation["instance_id"] == "inst-9"
    assert correlation["flow"] == "demo-flow"
    assert correlation["wizard"] == "demo-wizard"
    assert correlation["step_slug"] == "preflight"


def test_is_mutating_action() -> None:
    assert is_mutating_action("fetch") is False
    assert is_mutating_action("submit_flow") is True


@pytest.fixture
def executor() -> TransformExecutor:
    transform_registry.clear()
    autoload()
    return TransformExecutor()


def test_enrich_resource_with_resource_ref_and_action(executor: TransformExecutor) -> None:
    import palm.providers  # noqa: F401

    repo = DefinitionRepository()
    repo.register_resource(
        ResourceDefinition(
            id="resource-check-health",
            name="check-health",
            provider="rest",
            action="fetch",
            resource_id="health/check",
        )
    )
    resource = ResourceEngine()
    resource.initialize(definition_resolver=resource_definition_resolver(repo))
    try:
        result = executor.apply(
            "enrich_resource",
            {"tenant": "acme"},
            resource_ref="check-health",
            resource_engine=resource,
            target_field="health",
        )
        assert result.value["tenant"] == "acme"
        assert result.value["health"]["source"] == "rest"
        assert result.context.frames[-1].meta.get("resource_ref") == "check-health"
    finally:
        resource.shutdown()


def test_resource_engine_emit_includes_job_context() -> None:
    captured: list[dict] = []
    bus = EventEngine()
    bus.initialize()
    bus.subscribe("resource.completed", lambda e: captured.append(e.enriched_payload()))

    engine = ResourceEngine()
    engine.initialize(event_engine=bus)
    with bus.bind_context(EventContext(job_id="job-ctx", instance_id="inst-ctx")):
        result = engine.invoke(provider="rest", action="fetch", resource_id="x")
    engine.shutdown()
    bus.shutdown()

    assert result.success is True
    assert captured
    assert captured[-1]["job_id"] == "job-ctx"
    assert captured[-1]["instance_id"] == "inst-ctx"
