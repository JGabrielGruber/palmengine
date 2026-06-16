"""Tests for CQRS buses and instance projection."""

from __future__ import annotations

from palm.common.cqrs import CommandBus, QueryBus
from palm.common.cqrs.command import Command, SubmitFlowCommand
from palm.common.cqrs.projections.instance_index import (
    InstanceIndexProjection,
    InstanceReadModel,
)
from palm.common.cqrs.query import GetInstanceStatusQuery, ListInstancesQuery
from palm.core.event import Event
from palm.core.orchestration.events import OrchestrationEventType
from palm.core.storage import StorageEngine


def _storage() -> StorageEngine:
    from palm.storages.memory.backend import MemoryBackend

    engine = StorageEngine()
    engine.initialize()
    engine.select("memory")
    return engine


class _EchoHandler:
    def handle(self, command: Command) -> str:
        if isinstance(command, SubmitFlowCommand):
            return f"flow:{command.flow}"
        return "unknown"


def test_command_bus_dispatches_by_type() -> None:
    bus = CommandBus()
    bus.register(SubmitFlowCommand, _EchoHandler())
    result = bus.dispatch(SubmitFlowCommand(flow="demo"))
    assert result == "flow:demo"


def test_instance_projection_filters_list_query() -> None:
    storage = _storage()

    class _Manager:
        def list_summaries(self):
            return []

        def get(self, instance_id: str):
            raise RuntimeError("not found")

    projection = InstanceIndexProjection(storage, _Manager())
    projection._upsert(
        InstanceReadModel(
            instance_id="a",
            job_id="j1",
            status="RUNNING",
            flow_name="onboard",
            updated_at="2026-01-01T00:00:00+00:00",
        )
    )
    projection._upsert(
        InstanceReadModel(
            instance_id="b",
            job_id="j2",
            status="SUCCEEDED",
            flow_name="onboard",
            updated_at="2026-01-02T00:00:00+00:00",
        )
    )

    active = projection.list_instances(
        ListInstancesQuery(include_terminal=False, flow_name="onboard")
    )
    assert [row.instance_id for row in active] == ["a"]

    limited = projection.list_instances(ListInstancesQuery(limit=1))
    assert len(limited) == 1
    storage.shutdown()


def test_instance_projection_applies_status_event() -> None:
    storage = _storage()

    class _Manager:
        def list_summaries(self):
            return []

        def get(self, instance_id: str):
            raise RuntimeError("not found")

    projection = InstanceIndexProjection(storage, _Manager())
    projection.apply(
        Event(
            type=OrchestrationEventType.INSTANCE_STATUS_CHANGED,
            payload={
                "instance_id": "inst-1",
                "job_id": "job-1",
                "status": "WAITING_FOR_INPUT",
            },
        )
    )
    view = projection.get_instance(GetInstanceStatusQuery(instance_id="inst-1"))
    assert view is not None
    assert view.status == "WAITING_FOR_INPUT"
    storage.shutdown()