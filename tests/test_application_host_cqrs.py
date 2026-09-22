"""Tests for ApplicationHost CQRS integration."""

from __future__ import annotations

import time

from bundles.standard.app import ApplicationHost, DeploymentProfile, PalmSettings
from bundles.standard.app.host.events import HostEventType
from palm.common.cqrs.command import SubmitFlowCommand
from palm.common.cqrs.query import ListInstancesQuery
from tests.helpers.flows import spine_wizard


def test_execute_dispatches_submit_flow_command(settings: PalmSettings) -> None:
    host = ApplicationHost.for_mode("all_in_one", settings=settings)
    host.start()
    try:
        job = host.execute(
            SubmitFlowCommand(flow=spine_wizard("quick"), job_id="cqrs-1")
        )
        assert job.id == "cqrs-1"
        assert job.status.value == "WAITING_FOR_INPUT"
        host.provide_input("cqrs-1", "ok")
        job = host.runtime().orchestration.get_job("cqrs-1")
        assert job is not None
        assert job.status.value == "SUCCEEDED"
    finally:
        host.shutdown()


def test_application_host_exposes_domain_services(settings: PalmSettings) -> None:
    host = ApplicationHost.for_mode("all_in_one", settings=settings)
    host.start()
    try:
        assert host.system is not None
        assert host.definitions is not None
        assert host.execution is not None
        assert host.execution.flows is not None
        assert host.schemas is not None
        rows = host.system.list_jobs(limit=5)
        assert isinstance(rows, list)
        flows = host.definitions.list_flows()
        assert isinstance(flows, list)
    finally:
        host.shutdown()


def test_ask_list_instances_query(settings: PalmSettings) -> None:
    host = ApplicationHost.for_mode("all_in_one", settings=settings)
    host.start()
    try:
        rows = host.ask(ListInstancesQuery(include_terminal=True))
        assert isinstance(rows, list)
    finally:
        host.shutdown()


def test_router_round_robin_workers(settings: PalmSettings) -> None:
    profile = DeploymentProfile(master=True, worker=True, server=False, worker_count=2)
    host = ApplicationHost(settings=settings, profile=profile)
    host.start()
    try:
        routed = [host.router.route_job_runtime() for _ in range(4)]
        assert set(routed) == {"worker", "worker-1"}
        assert routed[0] != routed[1]
    finally:
        host.shutdown()


def test_recovery_emits_host_recovered(settings: PalmSettings) -> None:
    events: list[str] = []
    host = ApplicationHost.for_mode("all_in_one", settings=settings)
    host.event.subscribe("*", lambda e: events.append(e.type))
    host.start()
    host.shutdown()

    assert HostEventType.RECOVERED in events


def test_command_dispatched_event(settings: PalmSettings) -> None:
    events: list[dict] = []
    host = ApplicationHost.for_mode("all_in_one", settings=settings)
    host.event.subscribe(
        HostEventType.COMMAND_DISPATCHED,
        lambda e: events.append(dict(e.payload)),
    )
    host.start()
    try:
        host.execute(SubmitFlowCommand(flow=spine_wizard("quick")))
        assert events
        assert events[-1]["command"] == "SubmitFlowCommand"
    finally:
        host.shutdown()


def test_master_worker_routes_submit_to_worker(settings: PalmSettings) -> None:
    profile = DeploymentProfile(master=True, worker=True, server=False, worker_count=2)
    host = ApplicationHost(settings=settings, profile=profile)
    host.start()
    try:
        from palm.core.orchestration.exceptions import JobNotFoundError

        job = host.submit_flow(spine_wizard("quick"), job_id="routed-1")
        assert job.id == "routed-1"
        # Queued workers: wait until the job is waiting, then continue.
        waiting = False
        for _ in range(50):
            for name in ("worker", "worker-1"):
                try:
                    got = host.runtime(name).orchestration.get_job("routed-1")
                except JobNotFoundError:
                    continue
                if got.status.value == "WAITING_FOR_INPUT":
                    waiting = True
                    break
            if waiting:
                break
            time.sleep(0.05)
        assert waiting, "job never reached WAITING_FOR_INPUT on a worker"
        host.provide_input("routed-1", "ok")
        host.runtime("worker").wait_until_idle(timeout=2.0)
        host.runtime("worker-1").wait_until_idle(timeout=2.0)
        job = None
        for name in ("worker", "worker-1"):
            try:
                job = host.runtime(name).orchestration.get_job("routed-1")
                break
            except JobNotFoundError:
                continue
        assert job is not None
        assert job.status.value == "SUCCEEDED"
    finally:
        host.shutdown()
