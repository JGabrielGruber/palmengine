"""Tests for the Palm application layer."""

from __future__ import annotations

import pytest

from palm.app import PalmApp, PalmSettings
from palm.core.registry import pattern_registry, provider_registry, storage_registry
from palm.core.storage import StorageEngine
from palm.definitions.flow import FlowDefinition
from palm.runtimes.daemon import DaemonRuntime
from palm.runtimes.embedded import EmbeddedRuntime
from palm.runtimes.server import ServerRuntime


@pytest.fixture
def app() -> PalmApp:
    application = PalmApp(PalmSettings(load_example_definitions=False))
    application.bootstrap()
    return application


def test_bootstrap_registers_plugins(app: PalmApp) -> None:
    assert app.is_bootstrapped
    assert "wizard" in pattern_registry.names()
    assert "rest" in provider_registry.names()
    assert "memory" in storage_registry.names()


def test_create_embedded_runtime(app: PalmApp) -> None:
    runtime = app.create_runtime("embedded", autostart=True)
    assert isinstance(runtime, EmbeddedRuntime)
    assert runtime.is_started
    assert app.runtime() is runtime


def test_multiple_runtimes_share_storage(app: PalmApp) -> None:
    embedded = app.create_runtime("embedded", name="api", autostart=True)
    daemon = app.create_runtime("daemon", name="worker", autostart=True)

    assert embedded.storage is daemon.storage is app.storage
    assert set(app.running()) == {"api", "worker"}

    flow = FlowDefinition(name="shared", pattern="dag", options={"name": "shared"})
    embedded.repository.save_flow(flow)
    app.load_definitions(name="worker")
    assert daemon.repository.has_flow("shared")


def test_daemon_and_embedded_concurrent(app: PalmApp) -> None:
    embedded = app.create_runtime("embedded", name="cli", autostart=True)
    daemon = app.create_runtime("daemon", name="bg", autostart=True)

    flow = FlowDefinition(name="quick", pattern="dag", options={"name": "quick"})
    job = embedded.submit_flow(flow, job_id="dag-1")
    assert job.status.value == "SUCCEEDED"
    daemon.wait_until_idle(timeout=2.0)


def test_server_runtime_via_app(app: PalmApp) -> None:
    runtime = app.create_runtime("server", name="http", autostart=True, port=0, http=True)
    assert isinstance(runtime, ServerRuntime)
    assert runtime.base_url.startswith("http://127.0.0.1:")
    runtime.stop()


def test_load_definitions_hydrates_repository(app: PalmApp) -> None:
    app.settings = PalmSettings(load_example_definitions=True)
    app.create_runtime("embedded", autostart=True)
    count = app.load_definitions()
    assert count >= 0
    assert app.runtime().repository.list_flows() or count == 0


def test_shutdown_stops_runtimes_and_storage(app: PalmApp) -> None:
    app.create_runtime("embedded", autostart=True)
    app.create_runtime("daemon", name="worker", autostart=True)
    app.shutdown()
    assert len(app.running()) == 0
    assert not app.storage.is_initialized


def test_context_manager_shuts_down() -> None:
    with PalmApp(PalmSettings(load_example_definitions=False)) as application:
        application.create_runtime("embedded", autostart=True)
        assert application.running()
    storage = StorageEngine()
    assert not storage.is_initialized


def test_set_primary_runtime(app: PalmApp) -> None:
    app.create_runtime("embedded", name="first", autostart=True)
    app.create_runtime("daemon", name="second", autostart=True, set_primary=False)
    app.set_primary("second")
    assert isinstance(app.runtime(), DaemonRuntime)


def test_requires_bootstrap() -> None:
    application = PalmApp()
    with pytest.raises(RuntimeError, match="bootstrapped"):
        application.create_runtime("embedded")


def test_create_cli_host_registers_collapsed_runtime() -> None:
    from palm.app.session import create_cli_host
    from palm.runtimes.embedded import EmbeddedRuntime

    host = create_cli_host(settings=PalmSettings(load_example_definitions=False))
    try:
        assert host.is_started
        assert host.running_runtimes() == ["main"]
        runtime = host.runtime()
        assert isinstance(runtime, EmbeddedRuntime)
        assert host.app.list_processes() is not None
    finally:
        host.shutdown()
