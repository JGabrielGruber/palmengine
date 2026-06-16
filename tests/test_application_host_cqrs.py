"""Tests for ApplicationHost CQRS integration."""

from __future__ import annotations

from palm.app import ApplicationHost, HostProfile, PalmSettings
from palm.app.host.events import HostEventType
from palm.common.cqrs.command import SubmitFlowCommand
from palm.common.cqrs.query import ListInstancesQuery
from palm.definitions.flow import FlowDefinition


def test_execute_dispatches_submit_flow_command(settings: PalmSettings) -> None:
    host = ApplicationHost(settings=settings, profile=HostProfile.all_in_one())
    host.start()

    flow = FlowDefinition(name="quick", pattern="dag", options={"name": "quick"})
    job = host.execute(SubmitFlowCommand(flow=flow, job_id="cqrs-1"))
    assert job.id == "cqrs-1"
    assert job.status.value == "SUCCEEDED"

    host.shutdown()


def test_ask_list_instances_query(settings: PalmSettings) -> None:
    host = ApplicationHost(settings=settings, profile=HostProfile.all_in_one())
    host.start()

    rows = host.ask(ListInstancesQuery(include_terminal=True))
    assert isinstance(rows, list)

    host.shutdown()


def test_router_round_robin_workers(settings: PalmSettings) -> None:
    profile = HostProfile(master=True, worker=True, server=False, worker_count=2)
    host = ApplicationHost(settings=settings, profile=profile)
    host.start()

    routed = [host.router.route_job_runtime() for _ in range(4)]
    assert set(routed) == {"worker", "worker-1"}
    assert routed[0] != routed[1]

    host.shutdown()


def test_recovery_emits_host_recovered(settings: PalmSettings) -> None:
    events: list[str] = []
    host = ApplicationHost(settings=settings, profile=HostProfile.all_in_one())
    host.event.subscribe("*", lambda e: events.append(e.type))
    host.start()
    host.shutdown()

    assert HostEventType.RECOVERED in events


def test_command_dispatched_event(settings: PalmSettings) -> None:
    events: list[dict] = []
    host = ApplicationHost(settings=settings, profile=HostProfile.all_in_one())
    host.event.subscribe(
        HostEventType.COMMAND_DISPATCHED,
        lambda e: events.append(dict(e.payload)),
    )
    host.start()

    flow = FlowDefinition(name="quick", pattern="dag", options={"name": "quick"})
    host.execute(SubmitFlowCommand(flow=flow))
    assert events
    assert events[-1]["command"] == "SubmitFlowCommand"

    host.shutdown()


def test_master_worker_routes_submit_to_worker(settings: PalmSettings) -> None:
    profile = HostProfile(master=True, worker=True, server=False, worker_count=2)
    host = ApplicationHost(settings=settings, profile=profile)
    host.start()

    flow = FlowDefinition(name="quick", pattern="dag", options={"name": "quick"})
    job = host.submit_flow(flow, job_id="routed-1")
    host.runtime("worker").wait_until_idle(timeout=2.0)
    job = host.runtime("worker").orchestration.get_job("routed-1")
    assert job.status.value == "SUCCEEDED"

    host.shutdown()