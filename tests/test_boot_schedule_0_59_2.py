"""0.59.2 — stub schedule + modes (phase tables, walker, SystemLog reuse)."""

from __future__ import annotations

from bundles.standard.app.host.application_host import ApplicationHost
from bundles.standard.app.host.boot import BootMode, get_boot_mode, list_boot_modes
from bundles.standard.app.host.boot.system_log_phase import make_host_system_log_handler
from bundles.standard.app.host.roles import DeploymentProfile
from bundles.standard.app.settings import PalmSettings
from palm.system.boot import (
    HOST_PHASES,
    SYSTEM_PHASES,
    BootContext,
    host_phase_ids,
    schedule_catalog,
    system_phase_ids,
    walk_schedule,
)
from palm.system.log import (
    LEVEL_OPERATE,
    SystemLog,
    get_system_log,
    reset_system_log_for_tests,
    system_log_ready_handler,
)


def test_locked_phase_tables_order() -> None:
    host_ids = host_phase_ids()
    assert host_ids[0] == "host.system_log"
    assert "host.kernel.bootstrap" in host_ids
    assert "host.system.spawn" in host_ids
    assert host_ids.index("host.system.spawn") < host_ids.index("host.product.wire")
    assert host_ids[-1] == "host.ready"

    sys_ids = system_phase_ids()
    assert sys_ids[0] == "system.log.ready"
    assert "system.plugins.ensure" in sys_ids
    assert "system.install.bind" in sys_ids
    assert "system.planes.attach" in sys_ids
    assert "system.supervisor.wire" in sys_ids
    assert "system.background.start" in sys_ids
    assert sys_ids.index("system.install.bind") < sys_ids.index("system.planes.attach")
    assert sys_ids.index("system.planes.attach") < sys_ids.index(
        "system.supervisor.wire"
    )
    assert sys_ids.index("system.ready") < sys_ids.index("system.background.start")
    assert sys_ids[-1] == "system.background.start"

    catalog = schedule_catalog()
    assert len(catalog["host"]) == len(HOST_PHASES)
    assert len(catalog["system"]) == len(SYSTEM_PHASES)
    assert HOST_PHASES[0].seat == "implemented"
    assert SYSTEM_PHASES[0].seat == "implemented"
    # 0.59.3–.4: both schedules fully implemented seats.
    assert all(p.seat == "implemented" for p in HOST_PHASES)
    assert all(p.seat == "implemented" for p in SYSTEM_PHASES)


def test_walker_skips_missing_handlers_honestly() -> None:
    log = SystemLog(console=False, level=LEVEL_OPERATE, capacity=100)
    walked = walk_schedule(
        HOST_PHASES,
        handlers={},
        ctx=BootContext(schedule="host", mode="test"),
        log=log,
    )
    assert len(walked) == len(HOST_PHASES)
    assert all(w.outcome == "skip" for w in walked)
    # All seats implemented (0.59.4) — missing handler → no_handler, not fake ok.
    assert all(w.reason == "no_handler" for w in walked)
    assert "phase.skip" in log.events()
    # Same SystemLog narrative — no second path.
    assert all(r.event == "phase.skip" for r in log.recent() if r.event.startswith("phase."))


def test_walker_runs_implemented_system_log_seat() -> None:
    reset_system_log_for_tests()
    log = get_system_log()
    mode = BootMode.test()
    walked = walk_schedule(
        (HOST_PHASES[0],),
        {"host.system_log": make_host_system_log_handler(mode)},
        ctx=BootContext(schedule="host"),
        log=log,
    )
    assert walked[0].outcome == "ok"
    assert walked[0].phase == "host.system_log"
    events = log.events()
    assert "phase.start" in events
    assert "phase.end" in events
    assert "system_log.ready" in events
    assert log.level == mode.system_log_level


def test_walker_system_log_ready_standalone() -> None:
    reset_system_log_for_tests()
    log = get_system_log()
    walked = walk_schedule(
        (SYSTEM_PHASES[0],),
        {"system.log.ready": system_log_ready_handler},
        ctx=BootContext(schedule="system", runtime="main"),
        log=log,
    )
    assert walked[0].outcome == "ok"
    assert any(
        r.event == "system_log.ready" and r.fields.get("schedule") == "system"
        for r in log.recent()
    )


def test_walker_require_handlers_fails_missing_implemented() -> None:
    log = SystemLog(console=False, level=LEVEL_OPERATE)
    try:
        walk_schedule(
            (HOST_PHASES[0],),
            handlers={},
            log=log,
            require_handlers=True,
        )
        raise AssertionError("expected RuntimeError")
    except RuntimeError as exc:
        assert "host.system_log" in str(exc)
    assert "phase.fail" in log.events()


def test_boot_modes_registry() -> None:
    names = list_boot_modes()
    for expected in ("safe", "test", "dev", "prod", "cli", "mcp", "worker", "server"):
        assert expected in names
    safe = get_boot_mode("safe")
    assert safe.recover_on_start is False
    assert safe.composition.surfaces == ()
    dev = get_boot_mode("dev")
    assert dev.system_log_level == LEVEL_OPERATE
    assert "assist" in dev.composition.services


def test_host_with_boot_mode_test_skips_recover() -> None:
    reset_system_log_for_tests()
    settings = PalmSettings.for_tests(load_examples=False)
    host = ApplicationHost(settings=settings, boot_mode="test")
    assert host.boot_mode is not None
    assert host.boot_mode.name == "test"
    # Mode supplies composition when not passed explicitly.
    assert host.composition.services == BootMode.test().composition.services
    host.start()
    try:
        assert host.is_started
        # test mode: recover skipped
        assert any(
            r.event == "phase.skip"
            and r.fields.get("phase") == "host.recover"
            and r.fields.get("reason") == "mode_recover_off"
            for r in host.system_log.recent()
        )
        # early walker seat ran
        assert any(
            r.fields.get("phase") == "host.system_log" and r.event == "phase.start"
            for r in host.system_log.recent()
        )
        # doctor reports boot table + mode
        boot = host.control_plane_status()["boot"]
        assert boot["mode"] == "test"
        assert "host" in boot["phase_tables"]
        assert "system" in boot["phase_tables"]
        assert "safe" in boot["modes_available"]
    finally:
        host.shutdown()


def test_host_boot_mode_does_not_override_explicit_profile() -> None:
    settings = PalmSettings.for_tests(load_examples=False)
    host = ApplicationHost(
        settings=settings,
        boot_mode="safe",
        profile=DeploymentProfile.server_only(),
    )
    assert host.profile.server is True
    assert host.boot_mode is not None
    assert host.boot_mode.name == "safe"
    # composition still from mode (not overridden)
    assert host.composition.surfaces == ()


def test_default_host_still_has_no_boot_mode() -> None:
    """Legacy constructions stay green — mode is opt-in."""
    settings = PalmSettings.for_tests(load_examples=False)
    host = ApplicationHost(
        settings=settings,
        profile=DeploymentProfile.all_in_one(),
    )
    assert host.boot_mode is None
    host.start()
    try:
        # early system log seat still runs (no mode configure)
        phases = [
            r.fields.get("phase")
            for r in host.system_log.recent()
            if r.event == "phase.start" and r.fields.get("schedule") == "host"
        ]
        assert phases[0] == "host.system_log"
        assert host.control_plane_status()["boot"]["mode"] is None
    finally:
        host.shutdown()
