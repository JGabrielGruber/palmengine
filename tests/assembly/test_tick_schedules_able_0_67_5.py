"""0.67.5 — tick_schedules is drain-able; ready is not membership."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from bundles.standard.app.host.application_host import ApplicationHost
from bundles.standard.app.host.boot.modes import BootMode
from bundles.standard.app.settings import PalmSettings
from palm.core.structure import CAPABILITY_WORK_DRAIN, Observation, ObservationKind
from palm.system.log import reset_system_log_for_tests
from palm.system.runtime.base import BaseRuntime
from palm.system.structure.inventory import GATED_PATHS, READINESS_EDGES, admission_inventory
from palm.system.subsystems.planes.work.schedule import SCHEDULE_PREFIX


def _lean() -> PalmSettings:
    return PalmSettings.for_tests(load_examples=False)


def _due_schedule(rt: BaseRuntime, *, sid: str = "nightly", flow_id: str = "sched-flow") -> None:
    plane = rt.work_plane
    assert plane is not None
    plane.schedules.upsert(sid, flow_id=flow_id, interval_seconds=3600)
    key = f"{SCHEDULE_PREFIX}{sid}"
    entry = rt.storage.get(key)
    assert isinstance(entry, dict)
    entry["next_fire_at"] = (datetime.now(UTC) - timedelta(seconds=10)).isoformat()
    rt.storage.set(key, entry)


def _next_fire(rt: BaseRuntime, sid: str = "nightly") -> str:
    entry = rt.storage.get(f"{SCHEDULE_PREFIX}{sid}")
    assert isinstance(entry, dict)
    return str(entry["next_fire_at"])


def test_embedded_ready_does_not_fire_schedules() -> None:
    """Ready without work_drain is not schedule membership."""
    reset_system_log_for_tests()
    rt = BaseRuntime()
    rt.start(storage_backend="memory")
    try:
        assert rt.admission.may_run_business is True
        assert rt.admission.has_capability(CAPABILITY_WORK_DRAIN) is False
        plane = rt.work_plane
        assert plane is not None
        assert plane.is_able() is False
        _due_schedule(rt)
        before = _next_fire(rt)
        pending_before = plane.store.pending_count()
        assert plane.tick_schedules() == 0
        assert plane.store.pending_count() == pending_before
        assert _next_fire(rt) == before
    finally:
        rt.stop()


def test_cli_fires_schedules_when_drain_installed() -> None:
    reset_system_log_for_tests()
    rt = BaseRuntime()
    rt.start(
        storage_backend="memory",
        structure_definition_id="local.cli",
    )
    try:
        assert rt.admission.may_run_business is True
        assert rt.admission.has_capability(CAPABILITY_WORK_DRAIN) is True
        plane = rt.work_plane
        assert plane is not None
        assert plane.is_able() is True
        _due_schedule(rt)
        pending_before = plane.store.pending_count()
        fired = plane.tick_schedules()
        assert fired == 1
        assert plane.store.pending_count() == pending_before + 1
    finally:
        rt.stop()


def test_truth_home_down_does_not_fire_schedules() -> None:
    reset_system_log_for_tests()
    rt = BaseRuntime()
    rt.start(
        storage_backend="memory",
        structure_definition_id="local.cli",
    )
    try:
        plane = rt.work_plane
        assert plane is not None
        _due_schedule(rt)
        assert rt.structure is not None
        rt.structure.engine.observe(Observation(kind=ObservationKind.TRUTH_HOME_DOWN))
        assert rt.admission.may_run_business is False
        assert plane.is_able() is False
        before = _next_fire(rt)
        assert plane.tick_schedules() == 0
        assert _next_fire(rt) == before
    finally:
        rt.stop()


def test_embedded_host_tick_work_does_not_fire_schedules() -> None:
    reset_system_log_for_tests()
    host = ApplicationHost.for_mode(BootMode.safe(), settings=_lean())
    host.start()
    try:
        assert host.admission.may_run_business is True
        assert host.admission.has_capability(CAPABILITY_WORK_DRAIN) is False
        rt = host.runtime()
        plane = rt.work_plane
        assert plane is not None
        _due_schedule(rt)
        before = _next_fire(rt)
        assert host.tick_work(limit=5, schedules=True) == 0
        assert _next_fire(rt) == before
        assert plane.store.pending_count() == 0
    finally:
        host.shutdown()


def test_cli_host_tick_work_fires_schedules() -> None:
    reset_system_log_for_tests()
    host = ApplicationHost.for_mode(BootMode.cli(), settings=_lean())
    host.start()
    try:
        assert host.admission.has_capability(CAPABILITY_WORK_DRAIN) is True
        rt = host.runtime()
        plane = rt.work_plane
        assert plane is not None
        _due_schedule(rt)
        before = _next_fire(rt)
        n = host.tick_work(limit=5, schedules=True)
        assert n >= 1
        assert _next_fire(rt) != before
    finally:
        host.shutdown()


def test_inventory_tick_schedules_paid() -> None:
    gated = {row["id"] for row in GATED_PATHS}
    assert "work_plane.tick_schedules" in gated
    pretenders = {row["id"]: row["status"] for row in READINESS_EDGES}
    assert pretenders["work_plane.tick_schedules_edge"] == "paid_0_67_5"
    assert admission_inventory()["gated_count"] >= 1
