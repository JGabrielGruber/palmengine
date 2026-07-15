"""0.45.5 — event plane contract (buses, doctor, flow.session.* emission)."""

from __future__ import annotations

from examples.definitions.system.event_watch import _WATCH_FLOW, register_definitions as register_event_watch
from palm.app import ApplicationHost, PalmSettings
from tests.helpers.event_plane import emit_orchestration_event, runtime_event_engine


def test_event_plane_status_on_host() -> None:
    settings = PalmSettings.for_tests(load_examples=False)
    host = ApplicationHost(settings=settings)
    host.start()
    try:
        ep = host.event_plane_status()
        assert ep["orchestration_bus"] == "runtime"
        assert ep["inbound_internal_bus"] == "runtime"
        assert ep["journal_bus"] == "host"
        assert "flow.session.succeeded" in ep["orchestration_event_types"]

        cp = host.control_plane_status()
        assert cp["event_plane"]["orchestration_bus"] == "runtime"
    finally:
        host.shutdown()


def test_doctor_report_includes_event_plane() -> None:
    from palm.common.runtimes.server.diagnostics import build_doctor_report

    settings = PalmSettings.for_tests(load_examples=False)
    host = ApplicationHost(settings=settings)
    host.start()
    try:
        report = build_doctor_report(
            host.app.runtime(),
            control_plane=host.control_plane_status(),
        )
        ep = report["control_plane"]["event_plane"]
        assert ep["inbound_internal_bus"] == "runtime"
    finally:
        host.shutdown()


def _register_watch(host: ApplicationHost) -> None:
    register_event_watch(host.app.repository())
    host.reload_inbound_bindings()


def _drain_all(host: ApplicationHost) -> None:
    while host.work_drain.store.pending_count():
        host.work_drain.tick(limit=20)
    host._execution.flows.wait_until_idle(timeout=10.0)


def test_watch_records_flow_session_succeeded() -> None:
    settings = PalmSettings.for_tests(load_examples=False)
    host = ApplicationHost(settings=settings)
    host.start()
    try:
        _register_watch(host)
        emit_orchestration_event(
            host,
            "flow.session.succeeded",
            job_id="job-flow-1",
            flow_id="quick",
            flow="quick",
            status="SUCCEEDED",
        )
        _drain_all(host)
        result = host.invoke_resource("palm-system-event-log", action="get")
        value = (result.data or {}).get("value")
        assert isinstance(value, list)
        assert any(row.get("type") == "flow.session.succeeded" for row in value if isinstance(row, dict))
    finally:
        host.shutdown()


def test_watch_ingress_skips_self_flow_session_succeeded() -> None:
    settings = PalmSettings.for_tests(load_examples=False)
    host = ApplicationHost(settings=settings)
    host.start()
    try:
        _register_watch(host)
        host.invoke_resource(
            "palm-system-event-log",
            action="put",
            params={"value": []},
        )
        emit_orchestration_event(
            host,
            "flow.session.succeeded",
            job_id="job-self",
            flow_id=_WATCH_FLOW,
            flow=_WATCH_FLOW,
            status="SUCCEEDED",
        )
        _drain_all(host)
        pending = [
            intent
            for intent in host.work_drain.store.list_pending(limit=20)
            if intent.target == _WATCH_FLOW
        ]
        assert pending == []
    finally:
        host.shutdown()


def test_runtime_bus_is_not_host_bus() -> None:
    settings = PalmSettings.for_tests(load_examples=False)
    host = ApplicationHost(settings=settings)
    host.start()
    try:
        assert runtime_event_engine(host) is not host.event
    finally:
        host.shutdown()


def test_host_bus_emit_does_not_reach_internal_inbound() -> None:
    """Guard: orchestration tests must not use host.event for job.completed."""
    settings = PalmSettings.for_tests(load_examples=False)
    host = ApplicationHost(settings=settings)
    host.start()
    try:
        _register_watch(host)
        before = host.work_drain.store.pending_count()
        host.event.emit("job.completed", job_id="wrong-bus", flow="quick", status="SUCCEEDED")
        assert host.work_drain.store.pending_count() == before
    finally:
        host.shutdown()