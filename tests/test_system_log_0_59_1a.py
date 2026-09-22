"""System log (0.59.1a) — ring + boot phase narrative."""

from __future__ import annotations

from bundles.standard.app.host.application_host import ApplicationHost
from bundles.standard.app.host.roles import DeploymentProfile
from bundles.standard.app.settings import PalmSettings
from palm.system.log import (
    LEVEL_LIFECYCLE,
    SystemLog,
    configure_system_log,
    get_system_log,
    reset_system_log_for_tests,
)
from palm.system.runtime.base import BaseRuntime


def test_system_log_ring_and_level_filter() -> None:
    log = SystemLog(console=False, level=LEVEL_LIFECYCLE, capacity=50)
    assert log.emit(1, "boot.start", "hello") is not None
    assert log.emit(4, "detail.noise", "should drop") is None
    assert log.events() == ["boot.start"]
    assert log.recent_messages() == ["hello"]


def test_system_log_phase_context_ok_and_fail() -> None:
    log = SystemLog(console=False, level=LEVEL_LIFECYCLE, capacity=50)
    with log.phase("host", "host.demo"):
        pass
    events = log.events()
    assert events[0] == "phase.start"
    assert events[1] == "phase.end"
    assert log.recent()[-1].fields.get("duration_ms") is not None

    log.clear()
    try:
        with log.phase("host", "host.boom"):
            raise RuntimeError("nope")
    except RuntimeError:
        pass
    assert "phase.fail" in log.events()
    assert "nope" in (log.recent()[-1].fields.get("reason") or "")


def test_system_log_skip_requires_reason() -> None:
    log = SystemLog(console=False, level=LEVEL_LIFECYCLE)
    log.phase_skip("host", "host.surfaces.mount", reason="deployment.server_off")
    rec = log.recent()[-1]
    assert rec.event == "phase.skip"
    assert rec.fields["reason"] == "deployment.server_off"


def test_host_boot_writes_system_log_sequence() -> None:
    reset_system_log_for_tests()
    settings = PalmSettings.for_tests(load_examples=False)
    host = ApplicationHost(
        settings=settings,
        profile=DeploymentProfile.all_in_one(),
    )
    host.start()
    try:
        slog = host.system_log
        events = slog.events()
        assert "boot.start" in events
        assert "phase.start" in events
        assert "ready" in events
        phases = [
            r.fields.get("phase")
            for r in slog.recent()
            if r.event == "phase.start" and r.fields.get("schedule") == "host"
        ]
        assert "host.kernel.bootstrap" in phases
        assert "host.system.spawn" in phases
        assert "host.product.wire" in phases
        assert "host.recover" in phases
        # system schedule nested during spawn
        sys_phases = [
            r.fields.get("phase")
            for r in slog.recent()
            if r.event == "phase.start" and r.fields.get("schedule") == "system"
        ]
        assert "system.plugins.ensure" in sys_phases
        assert "system.planes.attach" in sys_phases
        # cold reader can sketch phenotype from messages
        messages = " ".join(slog.recent_messages())
        assert "host ready" in messages
        assert "system ready" in messages
    finally:
        host.shutdown()
        assert "shutdown.end" in get_system_log().events()


def test_system_alone_boot_log() -> None:
    reset_system_log_for_tests()
    rt = BaseRuntime()
    rt.start(storage_backend="memory")
    try:
        events = get_system_log().events()
        assert "boot.start" in events
        assert "ready" in events
        assert any(
            r.fields.get("phase") == "system.outbox.wire" and r.event == "phase.skip"
            for r in get_system_log().recent()
        )
    finally:
        rt.stop()


def test_configure_system_log_level() -> None:
    reset_system_log_for_tests()
    configure_system_log(level=0, console=False)
    assert get_system_log().emit(1, "x", "y") is None
    configure_system_log(level=3, console=False)
    assert get_system_log().emit(1, "x", "y") is not None
