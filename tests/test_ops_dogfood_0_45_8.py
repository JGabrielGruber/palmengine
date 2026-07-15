"""0.45.8 — ops dogfood: test isolation, invoke routes, control_plane ops."""

from __future__ import annotations

from pathlib import Path

from palm.app import ApplicationHost, PalmSettings
from palm.app.bootstrap import all_definition_roots
from palm.app.settings import PalmSettings as Settings
from palm.runtimes.server.surfaces.rest.execution.providers.routes import ROUTES


def test_all_definition_roots_skips_cwd_when_examples_disabled() -> None:
    settings = Settings.for_tests(load_examples=False)
    roots = all_definition_roots(settings)
    cwd_examples = (Path.cwd() / "examples" / "definitions").resolve()
    assert all(r.resolve() != cwd_examples for r in roots)


def test_all_definition_roots_includes_cwd_when_examples_enabled() -> None:
    settings = Settings.for_tests(load_examples=True)
    roots = all_definition_roots(settings)
    cwd_examples = (Path.cwd() / "examples" / "definitions").resolve()
    assert any(r.resolve() == cwd_examples for r in roots)


def test_host_without_examples_skips_cwd_system_pack() -> None:
    settings = PalmSettings.for_tests(load_examples=False)
    host = ApplicationHost(settings=settings)
    host.start()
    try:
        names = {flow.name for flow in host.app.list_flows()}
        assert "palm-system-watch-event" not in names
    finally:
        host.shutdown()


def test_control_plane_ops_and_drain_aliases() -> None:
    settings = PalmSettings.for_tests(load_examples=False)
    host = ApplicationHost(settings=settings)
    host.start()
    try:
        cp = host.control_plane_status()
        assert cp["work_drain_running"] == cp["work_drain_background"]
        ops = cp["ops"]
        assert "providers/{provider}/{resource_ref}/invoke" in ops["invoke_route"]
        assert "resources/{resource_ref}/invoke" in ops["invoke_route_short"]
        assert ops["storage_backend"] == "memory"
        assert ops["storage_durable"] is False
    finally:
        host.shutdown()


def test_ops_status_flags_event_log_on_memory() -> None:
    from examples.definitions.system.event_watch import register_definitions

    settings = PalmSettings.for_tests(load_examples=False)
    host = ApplicationHost(settings=settings)
    host.start()
    try:
        register_definitions(host.app.repository())
        ops = host.ops_status()
        assert ops["event_log_durable"] is False
        assert ops["event_log_note"] is not None
    finally:
        host.shutdown()


def test_rest_resource_invoke_route_registered() -> None:
    paths = {route.path for route in ROUTES}
    assert "/v1/api/resources/{resource_ref}/invoke" in paths
    assert "/v1/api/providers/{provider}/{resource_ref}/invoke" in paths