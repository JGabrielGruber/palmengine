"""Tests for FlowExecutionService, FlowSession, and ReplSession."""

from __future__ import annotations

from typing import Any

from palm.app import ApplicationHost, DeploymentProfile, PalmSettings
from palm.common.cqrs import CommandBus
from palm.common.cqrs.command import SubmitFlowCommand
from palm.common.cqrs.schemas import CqrsSchemaRegistry
from palm.core.orchestration import JobStatus
from palm.runtimes.server import ServerRuntime
from palm.runtimes.server.factory import build_server_context
from palm.services.execution import ExecutionService
from palm.services.execution.flows import FlowExecutionService, ReplSession
from palm.services.execution.processes import ProcessExecutionService
from palm.services.execution.providers import ProviderExecutionService


class _CommandBusStub:
    def __init__(self, *, job: Any | None = None) -> None:
        self._job = job
        self.dispatched: list[Any] = []

    def register(self, command_type: type, handler: Any) -> None:
        return None

    def dispatch(self, command: Any) -> Any:
        self.dispatched.append(command)
        if self._job is not None:
            return self._job
        raise RuntimeError("no job configured")


class _SystemStub:
    def __init__(self, views: dict[str, dict[str, Any]]) -> None:
        self._views = views

    def inspect_instance(self, session_id: str) -> dict[str, Any]:
        return self._views[session_id]


class _RuntimeStub:
    def __init__(self) -> None:
        self.idle_calls = 0

    def wait_until_idle(self, *, timeout: float = 5.0) -> bool:
        self.idle_calls += 1
        return True


def _flow_service(
    *,
    system: _SystemStub,
    commands: Any | None = None,
    runtime: _RuntimeStub | None = None,
) -> FlowExecutionService:
    registry = CqrsSchemaRegistry()
    return FlowExecutionService(
        commands=commands or CommandBus(),
        queries=CommandBus(),
        schemas=registry,
        system=system,  # type: ignore[arg-type]
        runtime=runtime or _RuntimeStub(),  # type: ignore[arg-type]
    )


def test_execution_flows_session_returns_handle() -> None:
    svc = _flow_service(system=_SystemStub({"inst_1": {"instance_id": "inst_1", "status": "RUNNING"}}))

    session = svc.session("approve", "inst_1")
    assert session.session_id == "inst_1"
    assert session.status()["status"] == "RUNNING"


def test_repl_session_tracks_active_session() -> None:
    svc = _flow_service(system=_SystemStub({"inst_1": {"instance_id": "inst_1"}}))
    repl = ReplSession(svc)

    session = repl.activate("inst_1", flow_id="approve")
    assert session.session_id == "inst_1"
    assert repl.active is not None
    assert repl.active.session_id == "inst_1"
    repl.clear()
    assert repl.active is None


def test_application_host_exposes_execution_service(settings: PalmSettings) -> None:
    host = ApplicationHost(settings=settings, profile=DeploymentProfile.all_in_one())
    host.start()

    assert host.execution is not None
    session = host.execution.flows.session(None, "missing")
    assert session.session_id == "missing"

    host.shutdown()


def test_run_wizard_and_input_integration() -> None:
    rt = ServerRuntime(host="127.0.0.1", port=0)
    rt.start(http=False)
    ctx = build_server_context(rt)
    try:
        session = ctx.execution.flows.run_wizard({"wizard": {"name": "onboard", "steps": 2}})
        assert session.session_id
        view = session.status()
        assert view.get("status") == JobStatus.WAITING_FOR_INPUT.value

        updated = session.input("Ada")
        assert updated.session_id == session.session_id
        assert updated.status in {
            JobStatus.WAITING_FOR_INPUT.value,
            JobStatus.SUCCEEDED.value,
            JobStatus.RUNNING.value,
        }
    finally:
        rt.stop()


def test_run_flow_dispatches_submit_flow_command() -> None:
    from dataclasses import dataclass, field

    @dataclass
    class _Job:
        id: str = "job-1"
        status: Any = field(default_factory=lambda: type("S", (), {"value": "RUNNING"})())
        metadata: dict[str, str] = field(default_factory=lambda: {"instance_id": "inst-1"})

    commands = _CommandBusStub(job=_Job())
    runtime = _RuntimeStub()
    svc = _flow_service(
        system=_SystemStub({"inst-1": {"instance_id": "inst-1", "job_id": "job-1"}}),
        commands=commands,
        runtime=runtime,
    )

    session = svc.run_flow("demo-flow")
    assert isinstance(commands.dispatched[0], SubmitFlowCommand)
    assert session.session_id == "inst-1"
    assert runtime.idle_calls == 1


def test_execution_service_coordinates_submodules() -> None:
    registry = CqrsSchemaRegistry()
    bus_kw = {"commands": CommandBus(), "queries": CommandBus(), "schemas": registry}
    system = _SystemStub({})
    execution = ExecutionService(
        flows=FlowExecutionService(**bus_kw, system=system),  # type: ignore[arg-type]
        providers=ProviderExecutionService(**bus_kw),
        processes=ProcessExecutionService(**bus_kw),
    )
    assert execution.flows is not None
    assert execution.providers is not None
    assert execution.processes is not None