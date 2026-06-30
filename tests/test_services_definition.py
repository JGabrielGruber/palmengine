"""Tests for DefinitionService."""

from __future__ import annotations

from typing import Any

import pytest

from palm.common.cqrs import CommandBus
from palm.common.cqrs.query import (
    GetFlowQuery,
    GetProcessQuery,
    ListFlowsQuery,
    ListProcessesQuery,
    Query,
)
from palm.common.cqrs.schemas import CqrsSchemaRegistry
from palm.common.services.definition import DefinitionService
from palm.common.services.errors import DefinitionNotFoundServiceError
from palm.definitions.flow import FlowDefinition
from palm.definitions.process import ProcessDefinition


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


class _RepositoryStub:
    def __init__(self, *, resources: list[Any] | None = None) -> None:
        self._resources = resources or []

    def list_resources(self) -> list[Any]:
        return self._resources

    def get_resource(self, ref: str, *, by_id: bool = False) -> Any:
        for resource in self._resources:
            if resource.name == ref or (by_id and resource.definition_id == ref):
                return resource
        from palm.common.exceptions import DefinitionNotFoundError

        raise DefinitionNotFoundError(ref)


def _sample_flow() -> FlowDefinition:
    return FlowDefinition(
        id="flow-1",
        name="demo",
        pattern="wizard",
        options={"steps": [{"slug": "one"}]},
    )


def _sample_process() -> ProcessDefinition:
    return ProcessDefinition(id="proc-1", name="demo-process", flows=[_sample_flow()])


def test_definition_list_flows_uses_list_flows_query() -> None:
    registry = CqrsSchemaRegistry()
    queries = _QueryBusStub({ListFlowsQuery: [_sample_flow()]})
    svc = DefinitionService(
        commands=CommandBus(),
        queries=queries,
        schemas=registry,
        repository=_RepositoryStub(),
    )

    rows = svc.list_flows(pattern="wizard")
    assert rows[0]["name"] == "demo"
    assert rows[0]["step_slugs"] == ["one"]
    assert isinstance(queries.asked[0], ListFlowsQuery)
    assert queries.asked[0].pattern == "wizard"


def test_definition_get_flow_raises_when_missing() -> None:
    registry = CqrsSchemaRegistry()
    queries = _QueryBusStub({GetFlowQuery: None})
    svc = DefinitionService(
        commands=CommandBus(),
        queries=queries,
        schemas=registry,
        repository=_RepositoryStub(),
    )

    with pytest.raises(DefinitionNotFoundServiceError) as exc_info:
        svc.get_flow("missing")
    assert exc_info.value.kind == "flow"
    assert exc_info.value.ref == "missing"


def test_definition_get_flow_verbose_and_summary() -> None:
    registry = CqrsSchemaRegistry()
    flow = _sample_flow()
    queries = _QueryBusStub({GetFlowQuery: flow})
    svc = DefinitionService(
        commands=CommandBus(),
        queries=queries,
        schemas=registry,
        repository=_RepositoryStub(),
    )

    summary = svc.get_flow("demo", verbose=False)
    detail = svc.get_flow("demo", verbose=True)
    assert summary["flow_id"] == "flow-1"
    assert detail["name"] == "demo"


def test_definition_list_and_get_processes() -> None:
    registry = CqrsSchemaRegistry()
    process = _sample_process()
    queries = _QueryBusStub(
        {
            ListProcessesQuery: [process],
            GetProcessQuery: process,
        }
    )
    svc = DefinitionService(
        commands=CommandBus(),
        queries=queries,
        schemas=registry,
        repository=_RepositoryStub(),
    )

    rows = svc.list_processes()
    assert rows[0]["process_id"] == "proc-1"
    detail = svc.get_process("demo-process")
    assert detail["name"] == "demo-process"


def test_definition_validate_flow() -> None:
    from palm.runtimes.server import ServerRuntime
    from palm.runtimes.server.factory import build_server_context

    rt = ServerRuntime(host="127.0.0.1", port=0)
    rt.start(http=False)
    ctx = build_server_context(rt)
    try:
        result = ctx.definition.validate_flow(
            {"wizard": {"name": "onboard", "steps": 2}},
            runtime=rt,
        )
        assert result["valid"] is True
        assert result["pattern"] == "wizard"
    finally:
        rt.stop()
