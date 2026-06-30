"""Tests for ExecutionService, InstanceSession, and ReplSession."""

from __future__ import annotations

from typing import Any

import pytest

from palm.app import ApplicationHost, HostProfile, PalmSettings
from palm.common.cqrs import CommandBus
from palm.common.cqrs.command import SubmitFlowCommand
from palm.common.cqrs.schemas import CqrsSchemaRegistry
from palm.common.services.execution import ExecutionService
from palm.common.services.internal import InternalService
from palm.common.services.session import ReplSession
from palm.core.orchestration import JobStatus
from palm.runtimes.server import ServerRuntime
from palm.runtimes.server.factory import build_server_context


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


class _InternalStub:
    def __init__(self, views: dict[str, dict[str, Any]]) -> None:
        self._views = views

    def inspect_instance(self, instance_id: str) -> dict[str, Any]:
        return self._views[instance_id]


class _RuntimeStub:
    def __init__(self) -> None:
        self.idle_calls = 0

    def wait_until_idle(self, *, timeout: float = 5.0) -> bool:
        self.idle_calls += 1
        return True


def test_execution_on_returns_session() -> None:
    registry = CqrsSchemaRegistry()
    internal = _InternalStub({"inst_1": {"instance_id": "inst_1", "status": "RUNNING"}})
    svc = ExecutionService(
        commands=CommandBus(),
        queries=CommandBus(),
        schemas=registry,
        internal=internal,  # type: ignore[arg-type]
        runtime=_RuntimeStub(),  # type: ignore[arg-type]
    )

    session = svc.on("inst_1")
    assert session.instance_id == "inst_1"
    assert session.status()["status"] == "RUNNING"


def test_repl_session_tracks_active_instance() -> None:
    registry = CqrsSchemaRegistry()
    internal = _InternalStub({"inst_1": {"instance_id": "inst_1"}})
    svc = ExecutionService(
        commands=CommandBus(),
        queries=CommandBus(),
        schemas=registry,
        internal=internal,  # type: ignore[arg-type]
        runtime=_RuntimeStub(),  # type: ignore[arg-type]
    )
    repl = ReplSession(svc)

    session = repl.activate("inst_1")
    assert session.instance_id == "inst_1"
    assert repl.active is not None
    assert repl.active.instance_id == "inst_1"
    repl.clear()
    assert repl.active is None


def test_application_host_exposes_execution_service(settings: PalmSettings) -> None:
    host = ApplicationHost(settings=settings, profile=HostProfile.all_in_one())
    host.start()

    assert host.execution is not None
    session = host.execution.on("missing")
    assert session.instance_id == "missing"

    host.shutdown()


def test_run_wizard_and_input_integration() -> None:
    rt = ServerRuntime(host="127.0.0.1", port=0)
    rt.start(http=False)
    ctx = build_server_context(rt)
    try:
        session = ctx.execution.run_wizard({"wizard": {"name": "onboard", "steps": 2}})
        assert session.instance_id
        view = session.status()
        assert view.get("status") == JobStatus.WAITING_FOR_INPUT.value

        updated = session.input("Ada")
        assert updated["instance_id"] == session.instance_id
        assert updated.get("status") in {
            JobStatus.WAITING_FOR_INPUT.value,
            JobStatus.SUCCEEDED.value,
            JobStatus.RUNNING.value,
        }
    finally:
        rt.stop()


def test_run_flow_dispatches_submit_flow_command() -> None:
    class _Job:
        id = "job-1"
        status = type("S", (), {"value": "RUNNING"})()
        metadata = {"instance_id": "inst-1"}

    registry = CqrsSchemaRegistry()
    commands = _CommandBusStub(job=_Job())
    internal = _InternalStub({"inst-1": {"instance_id": "inst-1", "job_id": "job-1"}})
    runtime = _RuntimeStub()
    svc = ExecutionService(
        commands=commands,  # type: ignore[arg-type]
        queries=CommandBus(),
        schemas=registry,
        internal=internal,  # type: ignore[arg-type]
        runtime=runtime,  # type: ignore[arg-type]
    )

    session = svc.run_flow("demo-flow")
    assert isinstance(commands.dispatched[0], SubmitFlowCommand)
    assert session.instance_id == "inst-1"
    assert runtime.idle_calls == 1