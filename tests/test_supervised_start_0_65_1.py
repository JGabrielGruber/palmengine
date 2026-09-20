"""0.65.1 — supervised start walks registration; seats carry outbox ports."""

from __future__ import annotations

import inspect

from palm.core.structure import LOCAL_CLI_ID, LOCAL_EMBEDDED_ID
from palm.system.boot.context import BootContext
from palm.system.interfaces.install import SystemInstall
from palm.system.log import reset_system_log_for_tests
from palm.system.runtime.base import BaseRuntime
from palm.system.structure.hands import CapabilitySeats
from palm.system.structure.phase_assemble import run as assemble_run
from palm.system.structure.seat import StructureSeat
from palm.system.subsystems.supervisor import (
    CallableSystemService,
    ServiceStartContext,
    SystemSupervisor,
)
from palm.system.subsystems.supervisor.definition import (
    ContinuousWireContext,
    register_work_drain,
    work_drain_may_start,
)
from palm.system.subsystems.supervisor.outbox_loop import OutboxLoopService
from palm.system.subsystems.supervisor.phase_background import (
    start_supervised_background,
)


class _FakePlane:
    def __init__(self) -> None:
        self.started = False

    def start_background(self) -> None:
        self.started = True

    def stop_background(self) -> None:
        self.started = False

    def status(self) -> dict[str, object]:
        return {"name": "work_drain", "running": self.started}


class _LeanShell:
    def __init__(self) -> None:
        self.structure = None
        self.install = None
        self.supervisor = None
        self.workload = None


def test_phase_source_has_no_organ_start_branches() -> None:
    from palm.system.subsystems.supervisor import phase_background

    src = inspect.getsource(phase_background)
    assert "want_drain" not in src
    assert "want_outbox" not in src
    assert 'start("work_drain")' not in src
    assert "start('work_drain')" not in src
    assert 'start("outbox")' not in src
    assert "start('outbox')" not in src
    assert 'name == "work_drain"' not in src
    assert 'name == "outbox"' not in src
    assert "structure_off:work_drain" not in src
    assert "ports_off:work_drain" not in src


def test_start_walks_registered_services() -> None:
    started: list[str] = []
    sup = SystemSupervisor(definitions=())
    sup.register(CallableSystemService("custom.loop", start=lambda: started.append("custom.loop")))
    result = start_supervised_background(sup, ServiceStartContext())
    assert result.skip_reason is None
    assert result.started == ["custom.loop"]
    assert started == ["custom.loop"]


def test_none_registered_when_supervisor_empty() -> None:
    result = start_supervised_background(
        SystemSupervisor(definitions=()),
        ServiceStartContext(),
    )
    assert result.started == []
    assert result.skip_reason == "none_registered"


def test_none_ready_when_registered_but_gated() -> None:
    sup = SystemSupervisor(definitions=())
    sup.register(CallableSystemService("gated.loop", may_start=lambda _ctx: False))
    result = start_supervised_background(sup, ServiceStartContext())
    assert result.started == []
    assert result.skip_reason == "none_ready"


def test_work_drain_may_start_follows_install_ports() -> None:
    board = SystemInstall()
    ctx = ServiceStartContext(install=board)
    assert work_drain_may_start(ctx) is False
    board.bind(work_plane=_FakePlane(), submit=lambda *_a: "x", able=lambda: True)
    assert work_drain_may_start(ctx) is True


def test_registered_outbox_starts_without_option() -> None:
    """Hand register is enough. enable_outbox_background is gone as start king."""
    svc = OutboxLoopService(processor=object(), store=object())  # type: ignore[arg-type]
    assert not hasattr(svc, "may_start") or svc.may_start(ServiceStartContext()) is True


def test_embedded_default_does_not_register_drain() -> None:
    reset_system_log_for_tests()
    rt = BaseRuntime()
    rt.start(storage_backend="memory")
    try:
        assert rt.supervisor is not None
        assert "work_drain" not in rt.supervisor.names()
        by_id = {w.phase: w for w in (rt._last_boot_walk or [])}
        assert by_id["system.background.start"].outcome == "skip"
        assert by_id["system.background.start"].reason == "none_registered"
    finally:
        rt.stop()


def test_cli_starts_drain_when_ports_bound() -> None:
    reset_system_log_for_tests()
    rt = BaseRuntime()
    rt.start(
        storage_backend="memory",
        structure_definition_id=LOCAL_CLI_ID,
    )
    try:
        assert rt.install.start_ports_bound() is True
        assert rt.supervisor is not None
        assert "work_drain" in rt.supervisor.names()
        by_id = {w.phase: w for w in (rt._last_boot_walk or [])}
        assert by_id["system.background.start"].outcome == "ok"
        assert set(rt.supervisor.status()["running"]) == {"work_drain", "outbox"}
    finally:
        rt.stop()


def test_capability_seats_carry_outbox_ports() -> None:
    seats = CapabilitySeats()
    assert seats.outbox_store is None
    assert seats.outbox_processor is None


def test_assemble_fills_outbox_ports_from_install_board() -> None:
    reset_system_log_for_tests()
    captured: list[CapabilitySeats] = []
    store, proc = object(), object()
    board = SystemInstall()
    board.bind(
        work_plane=_FakePlane(),
        outbox_store=store,
        outbox_processor=proc,
    )
    supervisor = SystemSupervisor(definitions=())
    ctx = BootContext(
        schedule="system",
        shell=_LeanShell(),
        install=board,
        supervisor=supervisor,
    )
    original = StructureSeat.materialize

    def _capture(self: StructureSeat, seats: CapabilitySeats) -> frozenset[str]:
        captured.append(seats)
        return original(self, seats)

    StructureSeat.materialize = _capture  # type: ignore[method-assign]
    try:
        assemble_run(ctx, {"structure_definition_id": LOCAL_EMBEDDED_ID})
    finally:
        StructureSeat.materialize = original  # type: ignore[method-assign]
    assert captured
    assert captured[0].outbox_store is store
    assert captured[0].outbox_processor is proc


def test_register_work_drain_wires_may_start() -> None:
    plane = _FakePlane()
    sup = SystemSupervisor(definitions=())
    register_work_drain(sup, ContinuousWireContext(work_plane=plane))
    svc = sup.get("work_drain")
    assert svc is not None
    board = SystemInstall()
    assert svc.may_start(ServiceStartContext(install=board)) is False
    board.bind(work_plane=plane, submit=lambda *_a: "x", able=lambda: True)
    assert svc.may_start(ServiceStartContext(install=board)) is True
