"""0.60.9 — lean system seats without ApplicationHost (dual-root honesty)."""

from __future__ import annotations

from palm.system.log import reset_system_log_for_tests
from palm.system.subsystems.planes.session.plane import SessionPlaneService
from palm.system.subsystems.planes.wait.plane import WaitPlaneService
from palm.system.subsystems.planes.work.plane import WorkPlaneService
from palm.system.runtime.base import BaseRuntime
from palm.system.subsystems.supervisor import SystemSupervisor


def test_base_runtime_reactive_seats_without_host() -> None:
    """Any started SystemInstance owns work/wait/session + supervisor."""
    reset_system_log_for_tests()
    rt = BaseRuntime()
    rt.start(storage_backend="memory")
    try:
        assert isinstance(rt.work_plane, WorkPlaneService)
        assert isinstance(rt.wait_plane, WaitPlaneService)
        assert isinstance(rt.session_plane, SessionPlaneService)
        assert isinstance(rt.supervisor, SystemSupervisor)
        names = set(rt.supervisor.names())
        assert "work_drain" not in names
        assert "outbox" not in names
        # Continuous services registered; not auto-started without flags.
        assert rt.supervisor.status()["running_count"] == 0
    finally:
        rt.stop()


def test_server_runtime_subclass_inherits_seats() -> None:
    from bundles.standard.runtimes.server.runtime import ServerRuntime

    reset_system_log_for_tests()
    rt = ServerRuntime()
    rt.start(storage_backend="memory")
    try:
        assert rt.work_plane is not None
        assert rt.supervisor is not None
        assert "work_drain" not in rt.supervisor.names()
    finally:
        rt.stop()
