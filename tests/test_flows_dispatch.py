"""Tests for FlowExecutionService.dispatch command chain."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from palm.common.cqrs import CommandBus
from palm.common.cqrs.command import SubmitFlowCommand
from palm.common.cqrs.schemas import CqrsSchemaRegistry
from palm.core.orchestration import JobStatus
from palm.services.execution.flows.schemas import SessionContext
from palm.services.execution.flows.service import FlowExecutionService


@dataclass
class _Flow:
    name: str = "approve"
    pattern: str = "wizard"
    definition_id: str = "approve"
    options: dict[str, Any] = field(default_factory=dict)
    has_state_schema: bool = False

    def catalog_summary(self) -> dict[str, Any]:
        return {
            "flow_id": self.definition_id,
            "name": self.name,
            "pattern": self.pattern,
            "has_state_schema": False,
        }


class _SystemStub:
    def __init__(self, views: dict[str, dict[str, Any]]) -> None:
        self._views = views

    def inspect_instance(self, session_id: str) -> dict[str, Any]:
        return self._views[session_id]


class _QueryBusStub:
    def __init__(self, *, flows: list[_Flow] | None = None) -> None:
        self._flows = flows or []

    def register(self, query_type: type, handler: Any) -> None:
        return None

    def ask(self, query: Any) -> Any:
        from palm.common.cqrs.query import GetFlowQuery, ListFlowsQuery

        if isinstance(query, ListFlowsQuery):
            return list(self._flows)
        if isinstance(query, GetFlowQuery):
            for flow in self._flows:
                if flow.definition_id == query.flow_id:
                    return flow
            return None
        raise RuntimeError(f"unexpected query: {query!r}")


class _CommandBusStub:
    def __init__(self, *, job: Any | None = None) -> None:
        self._job = job

    def register(self, command_type: type, handler: Any) -> None:
        return None

    def dispatch(self, command: Any) -> Any:
        if self._job is not None:
            return self._job
        raise RuntimeError("no job configured")


@dataclass
class _Job:
    id: str = "job-1"
    status: Any = field(default_factory=lambda: type("S", (), {"value": "RUNNING"})())
    metadata: dict[str, str] = field(default_factory=lambda: {"instance_id": "inst-1"})


def _service(
    *,
    system: _SystemStub,
    queries: _QueryBusStub | None = None,
    commands: _CommandBusStub | None = None,
) -> FlowExecutionService:
    registry = CqrsSchemaRegistry()
    return FlowExecutionService(
        commands=commands or CommandBus(),
        queries=queries or _QueryBusStub(),
        schemas=registry,
        system=system,  # type: ignore[arg-type]
        runtime=type("R", (), {"wait_until_idle": lambda self, timeout=5.0: True})(),  # type: ignore[arg-type]
    )


def test_dispatch_list_flows() -> None:
    svc = _service(
        system=_SystemStub({}),
        queries=_QueryBusStub(flows=[_Flow()]),
    )
    rows = svc.dispatch(["flows"])
    assert rows and rows[0]["flow_id"] == "approve"


def test_dispatch_describe_flow() -> None:
    svc = _service(
        system=_SystemStub({}),
        queries=_QueryBusStub(flows=[_Flow(name="onboard", definition_id="onboard")]),
    )
    row = svc.dispatch(["flows", "onboard"])
    assert row["name"] == "onboard"


def test_dispatch_session_context() -> None:
    svc = _service(
        system=_SystemStub(
            {
                "inst-1": {
                    "instance_id": "inst-1",
                    "status": JobStatus.RUNNING.value,
                    "metadata": {"pattern": "wizard", "flow": "approve"},
                }
            }
        ),
    )
    ctx = svc.dispatch(["flows", "approve", "session", "inst-1"])
    assert isinstance(ctx, SessionContext)
    assert ctx.session_id == "inst-1"
    assert ctx.flow_id == "approve"