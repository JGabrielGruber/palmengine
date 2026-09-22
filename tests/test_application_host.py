"""Tests for ApplicationHost role coordination."""

from __future__ import annotations

import time

import pytest

from bundles.standard.app import ApplicationHost, DeploymentProfile, PalmSettings
from bundles.standard.app.host.events import HostEventType
from palm.common.events import OutboxStore
from palm.core.event import Event
from bundles.standard.runtimes.daemon import DaemonRuntime
from bundles.standard.runtimes.embedded import EmbeddedRuntime
from bundles.standard.runtimes.server import ServerRuntime


def test_all_in_one_collapses_to_single_embedded(full_recovery_settings: PalmSettings) -> None:
    host = ApplicationHost(settings=full_recovery_settings, profile=DeploymentProfile.all_in_one())
    host.start()

    assert host.is_started
    assert host.running_runtimes() == ["main"]
    assert isinstance(host.runtime(), EmbeddedRuntime)
    rt = host.runtime()
    assert rt.supervisor is not None
    assert "outbox" in rt.supervisor.names()
    assert "outbox" in rt.supervisor.status()["running"]

    host.shutdown()


def test_collapsed_runtime_worker_ready_without_timeout(settings: PalmSettings) -> None:
    host = ApplicationHost(settings=settings, profile=DeploymentProfile.all_in_one())
    started = time.monotonic()
    host.start()
    elapsed = time.monotonic() - started

    assert host.last_recovery is not None
    assert host.last_recovery.get("workers_ready") is True
    assert host.last_recovery.get("workers") == ["main"]
    assert elapsed < 1.0

    host.shutdown()


def test_master_only_spawns_command_runtime(full_recovery_settings: PalmSettings) -> None:
    host = ApplicationHost(settings=full_recovery_settings, profile=DeploymentProfile.master_only())
    host.start()

    assert host.running_runtimes() == ["command"]
    assert isinstance(host.runtime(), EmbeddedRuntime)
    rt = host.runtime()
    assert rt.supervisor is not None
    assert "outbox" in rt.supervisor.names()

    host.shutdown()


def test_worker_only_spawns_daemon_workers(settings: PalmSettings) -> None:
    host = ApplicationHost(
        settings=settings,
        profile=DeploymentProfile.worker_only(count=2),
    )
    host.start()

    assert set(host.running_runtimes()) == {"worker", "worker-1"}
    assert isinstance(host.runtime(), DaemonRuntime)
    rt = host.runtime()
    assert rt.supervisor is not None
    assert "outbox" in rt.supervisor.names()
    assert "outbox" in rt.supervisor.status()["running"]

    host.shutdown()


def test_server_profile_spawns_server_runtime(settings: PalmSettings) -> None:
    host = ApplicationHost(
        settings=settings,
        profile=DeploymentProfile.server_only(port=0),
    )
    host.start()

    assert host.running_runtimes() == ["server"]
    runtime = host.runtime()
    assert isinstance(runtime, ServerRuntime)
    assert runtime.base_url.startswith("http://127.0.0.1:")
    assert runtime.supervisor is not None
    assert "outbox" in runtime.supervisor.names()
    assert "outbox" in runtime.supervisor.status()["running"]

    host.shutdown()


def test_master_and_worker_spawn_command_plus_daemon(settings: PalmSettings) -> None:
    profile = DeploymentProfile(master=True, worker=True, server=False, worker_count=2)
    host = ApplicationHost(settings=settings, profile=profile)
    host.start()

    assert set(host.running_runtimes()) == {"command", "worker", "worker-1"}
    assert isinstance(host.runtime("command"), EmbeddedRuntime)
    assert isinstance(host.runtime("worker"), DaemonRuntime)

    host.shutdown()


def test_host_emits_lifecycle_events(settings: PalmSettings) -> None:
    events: list[str] = []
    host = ApplicationHost(settings=settings, profile=DeploymentProfile.all_in_one())
    host.event.subscribe("*", lambda e: events.append(e.type))
    host.start()
    host.shutdown()

    assert HostEventType.STARTED in events
    assert HostEventType.SHUTDOWN in events
    assert HostEventType.RUNTIME_REGISTERED in events


def test_supervisor_outbox_drains_pending_entries(full_recovery_settings: PalmSettings) -> None:
    host = ApplicationHost(settings=full_recovery_settings, profile=DeploymentProfile.master_only())
    host.start()

    rt = host.runtime()
    store = rt.outbox_store
    assert store is not None
    store.enqueue(Event(type="job.completed", payload={"job_id": "j-1"}))
    assert store.pending_count() == 1

    svc = rt.supervisor.get("outbox")
    assert svc is not None
    processed = svc.process_once()
    assert processed == 1
    assert store.pending_count() == 0

    host.shutdown()


def test_all_in_one_submits_flow(settings: PalmSettings) -> None:
    from tests.helpers.flows import complete_spine_job

    host = ApplicationHost.for_mode("all_in_one", settings=settings)
    host.start()
    try:
        job = complete_spine_job(host, "dag-host-1", flow_name="quick")
        assert job.status.value == "SUCCEEDED"
    finally:
        host.shutdown()


def test_deployment_profile_from_settings_roles(settings: PalmSettings) -> None:
    settings.host_roles = ["master", "worker"]
    settings.worker_count = 2
    host = ApplicationHost(settings=settings)
    host.start()

    assert set(host.running_runtimes()) == {"command", "worker", "worker-1"}
    host.shutdown()


def test_palm_app_backward_compatible(settings: PalmSettings) -> None:
    from bundles.standard.app import PalmKernel

    app = PalmKernel(settings)
    app.bootstrap()
    runtime = app.create_runtime("embedded", autostart=True)
    assert runtime.is_started
    app.shutdown()


def test_context_manager(settings: PalmSettings) -> None:
    with ApplicationHost(settings=settings, profile=DeploymentProfile.all_in_one()) as host:
        assert host.is_started
        assert host.running_runtimes()
    assert not host.is_started


@pytest.mark.slow
def test_outbox_background_poll_marks_entries(full_recovery_settings: PalmSettings) -> None:
    host = ApplicationHost(
        settings=full_recovery_settings,
        profile=DeploymentProfile(
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
