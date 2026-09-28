"""0.60.2 — WorkPlaneService on system (enqueue / tick / attach)."""

from __future__ import annotations

from palm.core.work import WorkIntent
from palm.system.log import reset_system_log_for_tests
from palm.system.runtime.base import BaseRuntime
from palm.system.subsystems.planes.work.plane import WorkPlaneService
from tests.helpers.bound import bound_for_runtime


def test_work_plane_attach_enqueue_tick_hostless() -> None:
    reset_system_log_for_tests()
    submitted: list[tuple[str, dict]] = []

    rt = BaseRuntime()
    rt.start(
        drivers=bound_for_runtime(storage_backend="memory"), structure_definition_id="local.cli"
    )
    try:
        plane = rt.work_plane
        assert isinstance(plane, WorkPlaneService)
        assert plane.is_attached
        assert plane.status()["attached"] is True

        # Override submit so we do not need a catalog flow definition.
        plane._submit_flow = lambda fid, payload: submitted.append((fid, dict(payload)))

        intent_id = plane.enqueue(WorkIntent(kind="run_flow", target="demo-flow", payload={"k": 1}))
        assert intent_id
        assert plane.store.pending_count() >= 1

        n = plane.tick(limit=10, claimer_id="plane-test")
        assert n == 1
        assert submitted == [("demo-flow", {"k": 1})]
        assert plane.store.pending_count() == 0
        st = plane.status()
        assert st.get("claimer_id")
        assert "lease_seconds" in st
        assert "reclaimed" in st
    finally:
        rt.stop()
        assert rt.work_plane is None


def test_work_plane_depth_guard() -> None:
    reset_system_log_for_tests()
    rt = BaseRuntime()
    rt.start(drivers=bound_for_runtime(storage_backend="memory"))
    try:
        plane = rt.work_plane
        assert plane is not None
        plane._max_depth = 2
        ok = plane.enqueue(WorkIntent(kind="run_flow", target="a", depth=2))
        drop = plane.enqueue(WorkIntent(kind="run_flow", target="b", depth=3))
        assert ok != ""
        assert drop == ""
        assert plane.dropped_depth_count == 1
    finally:
        rt.stop()


def test_system_schedule_attaches_work_plane() -> None:
    reset_system_log_for_tests()
    rt = BaseRuntime()
    rt.start(drivers=bound_for_runtime(storage_backend="memory"))
    try:
        assert rt.work_plane is not None
        assert rt.wait_plane is not None
        assert rt.session_plane is not None
        assert rt.supervisor is not None
        assert "work_drain" not in rt.supervisor.names()
        by_id = {w.phase: w for w in (rt._last_boot_walk or [])}
        assert by_id["system.background.start"].outcome == "skip"
        assert by_id["system.background.start"].reason == "none_registered"
    finally:
        rt.stop()


def test_supervised_work_drain_background_when_enabled() -> None:
    reset_system_log_for_tests()
    rt = BaseRuntime()
    rt.start(
        drivers=bound_for_runtime(storage_backend="memory"), structure_definition_id="local.cli"
    )
    try:
        assert rt.supervisor is not None
        by_id = {w.phase: w for w in (rt._last_boot_walk or [])}
        assert by_id["system.background.start"].outcome == "ok"
        assert rt.work_plane is not None
        assert rt.work_plane.is_running is True
        assert set(rt.supervisor.status()["running"]) == {"work_drain", "outbox"}
        assert rt.work_plane.status().get("workers", 1) == 1
    finally:
        rt.stop()
        assert rt.work_plane is None


def test_work_plane_multi_worker_background() -> None:
    """0.62.4 — N continuous claimers; exclusive store (default path still N=1)."""
    reset_system_log_for_tests()
    submitted: list[str] = []
    lock = __import__("threading").Lock()

    rt = BaseRuntime()
    rt.start(
        drivers=bound_for_runtime(storage_backend="memory"),
        structure_definition_id="local.cli",
        work_plane_workers=3,
        work_plane_poll_interval=0.05,
        work_plane_batch_size=1,
    )
    try:
        plane = rt.work_plane
        assert plane is not None
        # Options may land via attach kwargs when install sees them; force if lean.
        if plane.workers < 3:
            plane.stop_background()
            plane._workers = 3
            plane.start_background()
        assert plane.is_running
        st = plane.status()
        assert st["workers"] == 3
        assert st["workers_alive"] == 3

        def _submit(fid: str, payload: dict) -> None:
            with lock:
                submitted.append(fid)

        plane._submit_flow = _submit
        for i in range(12):
            plane.enqueue(WorkIntent(id=f"mw{i}", kind="run_flow", target=f"flow-{i}"))
        # Wait for background drain
        import time

        deadline = time.monotonic() + 3.0
        while time.monotonic() < deadline:
            with lock:
                if len(submitted) >= 12:
                    break
            time.sleep(0.05)
        with lock:
            assert len(submitted) == 12
            assert len(set(submitted)) == 12
        assert plane.store.pending_count() == 0
    finally:
        rt.stop()
