"""0.60.1 — SystemSupervisor seat: registry, lifecycle, boot wire."""

from __future__ import annotations

from palm.system.boot import system_phase_ids
from palm.system.log import get_system_log, reset_system_log_for_tests
from palm.system.runtime.base import BaseRuntime
from palm.system.subsystems.supervisor import CallableSystemService, SystemSupervisor
from tests.helpers.bound import bound_for_runtime


def test_supervisor_register_start_stop_status() -> None:
    starts: list[str] = []
    stops: list[str] = []

    def _start() -> None:
        starts.append("work_drain")

    def _stop() -> None:
        stops.append("work_drain")

    svc = CallableSystemService(
        "work_drain",
        start=_start,
        stop=_stop,
        status=lambda: {"pending": 0},
    )
    sup = SystemSupervisor()
    assert sup.status()["service_count"] == 0

    sup.register(svc)
    assert sup.names() == ["work_drain"]
    assert sup.status()["registered"] == ["work_drain"]
    assert sup.status()["running_count"] == 0

    assert sup.start() == ["work_drain"]
    assert starts == ["work_drain"]
    assert sup.start("work_drain") == []  # idempotent
    assert starts == ["work_drain"]
    snap = sup.status()
    assert snap["running"] == ["work_drain"]
    assert snap["services"]["work_drain"]["running"] is True
    assert snap["services"]["work_drain"]["pending"] == 0

    assert sup.stop() == ["work_drain"]
    assert stops == ["work_drain"]
    assert sup.stop("work_drain") == []
    assert sup.status()["running_count"] == 0


def test_supervisor_unknown_service_raises() -> None:
    sup = SystemSupervisor()
    try:
        sup.start("nope")
        raise AssertionError("expected KeyError")
    except KeyError:
        pass
    try:
        sup.stop("nope")
        raise AssertionError("expected KeyError")
    except KeyError:
        pass


def test_system_boot_wires_empty_supervisor() -> None:
    reset_system_log_for_tests()
    rt = BaseRuntime()
    rt.start(drivers=bound_for_runtime(storage_backend="memory"))
    try:
        assert rt.is_started
        assert isinstance(rt.supervisor, SystemSupervisor)
        # Wire catalog does not freelance work_drain. Embedded DNA does not list it.
        assert "work_drain" not in rt.supervisor.names()
        assert rt.supervisor.status()["running_count"] == 0

        by_id = {w.phase: w for w in (rt._last_boot_walk or [])}
        assert by_id["system.supervisor.wire"].outcome == "ok"
        walked = [w.phase for w in (rt._last_boot_walk or [])]
        assert walked == list(system_phase_ids())
        assert system_phase_ids().index("system.planes.attach") < system_phase_ids().index(
            "system.supervisor.wire"
        )
        assert system_phase_ids().index("system.supervisor.wire") < system_phase_ids().index(
            "system.ready"
        )

        slog = get_system_log()
        assert "supervisor.wire" in slog.events()
    finally:
        rt.stop()
        assert rt.supervisor is None


def test_supervisor_stop_on_runtime_stop_stops_services() -> None:
    reset_system_log_for_tests()
    rt = BaseRuntime()
    rt.start(drivers=bound_for_runtime(storage_backend="memory"))
    stopped: list[str] = []
    try:
        assert rt.supervisor is not None
        rt.supervisor.register(
            CallableSystemService(
                "probe",
                start=lambda: None,
                stop=lambda: stopped.append("probe"),
            )
        )
        rt.supervisor.start("probe")
        assert rt.supervisor.status()["running"] == ["probe"]
    finally:
        rt.stop()
    assert stopped == ["probe"]
    assert rt.supervisor is None
