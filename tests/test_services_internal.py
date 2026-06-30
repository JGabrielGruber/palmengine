"""Tests for InternalService."""

from __future__ import annotations

from typing import Any

from palm.common.cqrs import CommandBus
from palm.common.cqrs.query import (
    GetJobContextQuery,
    InspectInstanceQuery,
    ListJobStatusQuery,
    Query,
)
from palm.common.cqrs.schemas import CqrsSchemaRegistry
from palm.common.services.errors import InstanceNotFoundServiceError
from palm.common.services.internal import InternalService


class _QueryBusStub:
    def __init__(self, responses: dict[type, Any]) -> None:
        self._responses = responses
        self.asked: list[Query] = []

    def register(self, query_type: type, handler: Any) -> None:
        return None

    def ask(self, query: Query) -> Any:
        self.asked.append(query)
        handler = self._responses.get(type(query))
        if callable(handler):
            return handler(query)
        return handler


def test_internal_list_jobs_uses_list_job_status_query() -> None:
    registry = CqrsSchemaRegistry()
    queries = _QueryBusStub({ListJobStatusQuery: [{"job_id": "j1", "status": "RUNNING"}]})
    svc = InternalService(commands=CommandBus(), queries=queries, schemas=registry)

    rows = svc.list_jobs(status="RUNNING", limit=5)
    assert rows == [{"job_id": "j1", "status": "RUNNING"}]
    assert isinstance(queries.asked[0], ListJobStatusQuery)
    assert queries.asked[0].status == "RUNNING"
    assert queries.asked[0].limit == 5


def test_internal_inspect_instance_uses_inspect_query() -> None:
    registry = CqrsSchemaRegistry()
    queries = _QueryBusStub(
        {
            InspectInstanceQuery: {"instance_id": "inst_1", "pattern": "wizard"},
        }
    )
    svc = InternalService(commands=CommandBus(), queries=queries, schemas=registry)

    view = svc.inspect_instance("inst_1")
    assert view["pattern"] == "wizard"
    assert isinstance(queries.asked[0], InspectInstanceQuery)


def test_internal_inspect_instance_raises_when_missing() -> None:
    registry = CqrsSchemaRegistry()
    queries = _QueryBusStub(
        {
            InspectInstanceQuery: None,
        }
    )
    svc = InternalService(commands=CommandBus(), queries=queries, schemas=registry)

    try:
        svc.inspect_instance("missing")
        raise AssertionError("expected InstanceNotFoundServiceError")
    except InstanceNotFoundServiceError as exc:
        assert exc.instance_id == "missing"


def test_internal_inspect_job_uses_job_context_query() -> None:
    registry = CqrsSchemaRegistry()
    queries = _QueryBusStub({GetJobContextQuery: {"found": True, "job_id": "j1"}})
    svc = InternalService(commands=CommandBus(), queries=queries, schemas=registry)

    payload = svc.inspect_job("j1")
    assert payload["job_id"] == "j1"
    assert isinstance(queries.asked[0], GetJobContextQuery)
