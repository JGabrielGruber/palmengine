"""0.59.4 — ApplicationHost walks the full host phase table."""

from __future__ import annotations

from bundles.standard.app.host.application_host import ApplicationHost
from bundles.standard.app.host.roles import DeploymentProfile
from bundles.standard.app.settings import PalmSettings
from palm.system.boot import HOST_PHASES, host_phase_ids
from palm.system.log import get_system_log, reset_system_log_for_tests


def test_host_start_walks_full_phase_table() -> None:
    reset_system_log_for_tests()
    settings = PalmSettings.for_tests(load_examples=False)
    host = ApplicationHost(
        settings=settings,
        profile=DeploymentProfile.all_in_one(),
    )
    host.start()
    try:
        assert host.is_started
        assert host._last_boot_walk is not None
        walked_ids = [w.phase for w in host._last_boot_walk]
        assert walked_ids == list(host_phase_ids())
        by_id = {w.phase: w for w in host._last_boot_walk}
        assert by_id["host.system_log"].outcome == "ok"
        assert by_id["host.kernel.bootstrap"].outcome == "ok"
        assert by_id["host.system.spawn"].outcome == "ok"
        assert by_id["host.product.wire"].outcome == "ok"
        # all_in_one collapsed: no server surface
        assert by_id["host.surfaces.mount"].outcome == "skip"
        assert by_id["host.surfaces.mount"].reason == "deployment.server_off"
        assert "host.projections.attach" not in by_id
        assert by_id["host.recover"].outcome == "ok"
        assert by_id["host.ready"].outcome == "ok"

        slog = get_system_log()
        assert "boot.start" in slog.events()
        assert "ready" in slog.events()
        host_starts = [
            r.fields.get("phase")
            for r in slog.recent()
            if r.event == "phase.start" and r.fields.get("schedule") == "host"
        ]
        assert host_starts[0] == "host.system_log"
        assert "host.system.spawn" in host_starts
        assert "host.ready" in host_starts
        # Nested system schedule during spawn
        sys_starts = [
            r.fields.get("phase")
            for r in slog.recent()
            if r.event == "phase.start" and r.fields.get("schedule") == "system"
        ]
        assert "system.plugins.ensure" in sys_starts
        assert "system.planes.attach" in sys_starts
        assert "system.background.start" in sys_starts
    finally:
        host.shutdown()


def test_host_boot_mode_test_walk_skips_recover() -> None:
    reset_system_log_for_tests()
    settings = PalmSettings.for_tests(load_examples=False)
    host = ApplicationHost(settings=settings, boot_mode="test")
    host.start()
    try:
        by_id = {w.phase: w for w in (host._last_boot_walk or [])}
        assert by_id["host.recover"].outcome == "skip"
        assert by_id["host.recover"].reason == "mode_recover_off"
        assert by_id["host.ready"].outcome == "ok"
        boot = host.control_plane_status()["boot"]
        assert boot["mode"] == "test"
    finally:
        host.shutdown()


def test_all_host_phases_implemented() -> None:
    assert all(p.seat == "implemented" for p in HOST_PHASES)
    assert host_phase_ids()[0] == "host.system_log"
    assert host_phase_ids()[-1] == "host.ready"
