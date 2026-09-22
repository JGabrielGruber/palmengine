"""
0.61 — vitality dogfood through ApplicationHost → primary system instance.

Host is packaging. Eyes read the **system** after spawn.
This is the proof that composition-root start seats a living kernel we can see.

Does **not** invent host dual APIs as vitality law.
"""

from __future__ import annotations

from bundles.standard.app.host.application_host import ApplicationHost
from bundles.standard.app.host.roles import DeploymentProfile
from bundles.standard.app.settings import PalmSettings
from palm.system.log import reset_system_log_for_tests
from palm.system.vitality import (
    SEAT_BOOT_MEMBERSHIP,
    SEAT_EXECUTION,
    SEAT_INSTALL,
    SEAT_PLANES,
    SEAT_SESSION_PLANE,
    SEAT_SUPERVISOR,
    SEAT_SYSTEM_LOG,
    SEAT_WAIT_PLANE,
    SEAT_WORK_PLANE,
    STATE_OK,
    project,
    project_top,
    seat_walk,
    walk_result,
)


def _started_host() -> ApplicationHost:
    reset_system_log_for_tests()
    settings = PalmSettings.for_tests(load_examples=False)
    host = ApplicationHost(
        settings=settings,
        profile=DeploymentProfile.all_in_one(),
        boot_mode="test",
    )
    host.start()
    return host


def test_host_primary_seat_walk_sees_kernel_seats() -> None:
    """After host.start, primary runtime walk shows planes, install, supervisor."""
    host = _started_host()
    try:
        rt = host.runtime()
        assert rt is not None
        assert rt.is_started

        result = walk_result(rt)
        by_id = result.by_id()

        # Interfaces + subsystems that boot seats.
        for seat_id in (
            SEAT_PLANES,
            SEAT_WAIT_PLANE,
            SEAT_SESSION_PLANE,
            SEAT_WORK_PLANE,
            SEAT_SUPERVISOR,
            SEAT_EXECUTION,
            SEAT_INSTALL,
            SEAT_SYSTEM_LOG,
        ):
            assert seat_id in by_id, f"missing seat {seat_id}"
            assert by_id[seat_id].present is True, f"{seat_id} not present"
            assert by_id[seat_id].state == STATE_OK, f"{seat_id} state={by_id[seat_id].state}"

        # Install board raw: collaborator ports bound after system.install.bind.
        install = by_id[SEAT_INSTALL]
        ports = (install.meta.get("raw") or {}).get("ports") or {}
        assert ports.get("orchestration") is True
        assert ports.get("storage") is True
        assert ports.get("submit") is True

        # System boot walk is on the instance (not host walk).
        assert SEAT_BOOT_MEMBERSHIP in by_id
        assert by_id[SEAT_BOOT_MEMBERSHIP].present is True

        # Host walk is separate (composition root); eyes on host shell are not law yet.
        assert host._last_boot_walk is not None
        assert any(w.phase == "host.system.spawn" for w in host._last_boot_walk)
    finally:
        host.shutdown()


def test_host_primary_projection_top_matches_walk() -> None:
    """project_top on host primary is the operate-shaped fold of the same seats."""
    host = _started_host()
    try:
        rt = host.runtime()
        top = project_top(rt)
        present = set(top["summary"]["present_ids"])
        assert SEAT_WAIT_PLANE in present
        assert SEAT_INSTALL in present
        assert SEAT_PLANES in present

        rows = seat_walk(rt)
        walk_present = {r["seat_id"] for r in rows if r["present"]}
        # Projection present set ⊆ walk present (may filter intention caps only).
        assert present <= walk_present or present == walk_present

        snap = project(rt)
        assert snap.summary["present_count"] >= 8
        install_row = next(s for s in snap.seats if s.seat_id == SEAT_INSTALL)
        assert install_row.present is True
    finally:
        host.shutdown()


def test_host_has_no_vitality_seat_yet() -> None:
    """Honesty: ApplicationHost is not a vitality seat; eyes are system-only today."""
    host = _started_host()
    try:
        # Walking the *host* as if it were a system instance is not the product API.
        # Absent/empty is fine; we assert the *primary* is the dogfood target.
        rt = host.runtime()
        sys_ids = {r["seat_id"] for r in seat_walk(rt) if r["present"]}
        assert SEAT_PLANES in sys_ids
        # Host is packaging — no install board on the host object itself.
        assert getattr(host, "install", None) is None
    finally:
        host.shutdown()
