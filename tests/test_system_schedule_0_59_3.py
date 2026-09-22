"""0.59.3 — BaseRuntime walks the full system phase table."""

from __future__ import annotations

from bundles.standard.app.bootstrap import runtime_start_options
from bundles.standard.app.settings import PalmSettings
from palm.system.boot import SYSTEM_PHASES, system_phase_ids
from palm.system.log import get_system_log, reset_system_log_for_tests
from palm.system.subsystems.planes.session.plane import SessionPlaneService
from palm.system.subsystems.planes.wait.plane import WaitPlaneService
from palm.system.runtime.base import BaseRuntime


def test_system_start_walks_full_phase_table() -> None:
    reset_system_log_for_tests()
    rt = BaseRuntime()
    rt.start(storage_backend="memory")
    try:
        assert rt.is_started
        assert rt._last_boot_walk is not None
        walked_ids = [w.phase for w in rt._last_boot_walk]
        assert walked_ids == list(system_phase_ids())
        # All seats visited; optional may skip.
        by_id = {w.phase: w for w in rt._last_boot_walk}
        assert by_id["system.log.ready"].outcome == "ok"
        assert by_id["system.plugins.ensure"].outcome == "ok"
        assert by_id["system.engines.init"].outcome == "ok"
        assert by_id["system.storage.select"].outcome == "ok"
        assert by_id["system.outbox.wire"].outcome == "skip"
        assert by_id["system.outbox.wire"].reason == "capability_off:outbox"
        assert by_id["system.hooks.install"].outcome == "ok"
        assert by_id["system.orchestration.start"].outcome == "ok"
        assert by_id["system.install.bind"].outcome == "ok"
        assert by_id["system.planes.attach"].outcome == "ok"
        assert by_id["system.supervisor.wire"].outcome == "ok"
        assert by_id["system.ready"].outcome == "ok"
        assert isinstance(rt.wait_plane, WaitPlaneService)
        assert isinstance(rt.session_plane, SessionPlaneService)
        assert rt.work_plane is not None
        assert rt.supervisor is not None

        slog = get_system_log()
        assert "boot.start" in slog.events()
        assert "ready" in slog.events()
        starts = [
            r.fields.get("phase")
            for r in slog.recent()
            if r.event == "phase.start" and r.fields.get("schedule") == "system"
        ]
        # Walker emits phase.start for every seat including optional (then skip).
        assert starts[0] == "system.log.ready"
        assert "system.plugins.ensure" in starts
        assert "system.storage.select" in starts
        assert "system.planes.attach" in starts
        assert "system.ready" in starts
        assert any(
            r.event == "phase.skip"
            and r.fields.get("phase") == "system.outbox.wire"
            and r.fields.get("reason") == "capability_off:outbox"
            for r in slog.recent()
        )
    finally:
        rt.stop()


def test_system_start_with_outbox_ok() -> None:
    reset_system_log_for_tests()
    rt = BaseRuntime()
    rt.start(storage_backend="memory", structure_definition_id="local.cli")
    try:
        assert rt.outbox_store is not None
        by_id = {w.phase: w for w in (rt._last_boot_walk or [])}
        assert by_id["system.outbox.wire"].outcome == "ok"
    finally:
        rt.stop()


def test_system_spine_via_settings_options() -> None:
    """Spine options path still attaches planes after walker cutover."""
    settings = PalmSettings.for_tests(load_examples=False)
    rt = BaseRuntime()
    rt.start(**runtime_start_options(settings))
    try:
        assert rt.is_started
        assert rt.wait_plane is not None
        assert rt.session_plane is not None
        assert len(rt._last_boot_walk or []) == len(SYSTEM_PHASES)
    finally:
        rt.stop()


def test_all_system_phases_implemented() -> None:
    assert all(p.seat == "implemented" for p in SYSTEM_PHASES)
    assert system_phase_ids()[0] == "system.log.ready"
    assert system_phase_ids()[-1] == "system.background.start"
