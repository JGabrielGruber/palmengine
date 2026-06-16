"""Tests for ApplicationHost role coordination."""

from __future__ import annotations

import time

import pytest

from palm.app import ApplicationHost, HostProfile, PalmSettings
from palm.app.host.events import HostEventType
from palm.common.events import OutboxStore
from palm.core.event import Event
from palm.definitions.flow import FlowDefinition
from palm.runtimes.daemon import DaemonRuntime
from palm.runtimes.embedded import EmbeddedRuntime
from palm.runtimes.server import ServerRuntime


@pytest.fixture
def settings() -> PalmSettings:
    return PalmSettings(load_example_definitions=False)


def test_all_in_one_collapses_to_single_embedded(settings: PalmSettings) -> None:
    host = ApplicationHost(settings=settings, profile=HostProfile.all_in_one())
    host.start()

    assert host.is_started
    assert host.running_runtimes() == ["main"]
    assert isinstance(host.runtime(), EmbeddedRuntime)
    assert host.outbox_service is not None
    assert host.outbox_service.is_running

    host.shutdown()


def test_master_only_spawns_command_runtime(settings: PalmSettings) -> None:
    host = ApplicationHost(settings=settings, profile=HostProfile.master_only())
    host.start()

    assert host.running_runtimes() == ["command"]
    assert isinstance(host.runtime(), EmbeddedRuntime)
    assert host.outbox_service is not None

    host.shutdown()


def test_worker_only_spawns_daemon_workers(settings: PalmSettings) -> None:
    host = ApplicationHost(
        settings=settings,
        profile=HostProfile.worker_only(count=2),
    )
    host.start()

    assert set(host.running_runtimes()) == {"worker", "worker-1"}
    assert isinstance(host.runtime(), DaemonRuntime)
    assert host.outbox_service is None

    host.shutdown()


def test_server_profile_spawns_server_runtime(settings: PalmSettings) -> None:
    host = ApplicationHost(
        settings=settings,
        profile=HostProfile.server_only(port=0),
    )
    host.start()

    assert host.running_runtimes() == ["server"]
    runtime = host.runtime()
    assert isinstance(runtime, ServerRuntime)
    assert runtime.base_url.startswith("http://127.0.0.1:")
    assert host.outbox_service is None

    host.shutdown()


def test_master_and_worker_spawn_command_plus_daemon(settings: PalmSettings) -> None:
    profile = HostProfile(master=True, worker=True, server=False, worker_count=2)
    host = ApplicationHost(settings=settings, profile=profile)
    host.start()

    assert set(host.running_runtimes()) == {"command", "worker", "worker-1"}
    assert isinstance(host.runtime("command"), EmbeddedRuntime)
    assert isinstance(host.runtime("worker"), DaemonRuntime)

    host.shutdown()


def test_host_emits_lifecycle_events(settings: PalmSettings) -> None:
    events: list[str] = []
    host = ApplicationHost(settings=settings, profile=HostProfile.all_in_one())
    host.event.subscribe("*", lambda e: events.append(e.type))
    host.start()
    host.shutdown()

    assert HostEventType.STARTED in events
    assert HostEventType.SHUTDOWN in events
    assert HostEventType.RUNTIME_REGISTERED in events


def test_outbox_service_drains_pending_entries(settings: PalmSettings) -> None:
    host = ApplicationHost(settings=settings, profile=HostProfile.master_only())
    host.start()

    store = host.outbox_service.store
    store.enqueue(Event(type="job.completed", payload={"job_id": "j-1"}))
    assert store.pending_count() == 1

    processed = host.outbox_service.process_once()
    assert processed == 1
    assert store.pending_count() == 0

    host.shutdown()


def test_all_in_one_submits_flow(settings: PalmSettings) -> None:
    host = ApplicationHost(settings=settings, profile=HostProfile.all_in_one())
    host.start()

    flow = FlowDefinition(name="quick", pattern="dag", options={"name": "quick"})
    job = host.submit_flow(flow, job_id="dag-host-1")
    assert job.status.value == "SUCCEEDED"

    host.shutdown()


def test_host_profile_from_settings_roles(settings: PalmSettings) -> None:
    settings.host_roles = ["master", "worker"]
    settings.worker_count = 2
    host = ApplicationHost(settings=settings)
    host.start()

    assert set(host.running_runtimes()) == {"command", "worker", "worker-1"}
    host.shutdown()


def test_palm_app_backward_compatible(settings: PalmSettings) -> None:
    from palm.app import PalmApp

    app = PalmApp(settings)
    app.bootstrap()
    runtime = app.create_runtime("embedded", autostart=True)
    assert runtime.is_started
    app.shutdown()


def test_context_manager(settings: PalmSettings) -> None:
    with ApplicationHost(settings=settings, profile=HostProfile.all_in_one()) as host:
        assert host.is_started
        assert host.running_runtimes()
    assert not host.is_started


def test_outbox_background_poll_marks_entries(settings: PalmSettings) -> None:
    host = ApplicationHost(
        settings=settings,
        profile=HostProfile(
            master=True,
            worker=False,
            outbox_poll_interval=0.05,
        ),
    )
    host.start()
    store = OutboxStore(host.storage)
    store.enqueue(Event(type="wizard.completed", payload={"wizard": "demo"}))
    deadline = time.monotonic() + 2.0
    while time.monotonic() < deadline and store.pending_count() > 0:
        time.sleep(0.05)
    assert store.pending_count() == 0
    host.shutdown()