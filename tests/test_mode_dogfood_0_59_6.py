"""0.59.6 — Mode dogfood: ``safe`` + ``test`` green in CI.

Green bar for this slice:
- Both modes boot via :meth:`ApplicationHost.for_mode` (no private internals).
- Phenotype: embedded membership, recover off, background off.
- SystemLog level defaults applied (and test console quiet).
- Spine: submit a tiny flow → SUCCEEDED on both modes.
- Doctor reports mode, membership, and ``last_walk``.
"""

from __future__ import annotations

import pytest

from palm.app.host.application_host import ApplicationHost
from palm.app.host.boot.modes import BootMode, get_boot_mode
from palm.app.host.composition import composition_profile_from_name
from palm.common.cqrs.command import SubmitFlowCommand
from palm.definitions.flow import FlowDefinition
from palm.system.log import (
    LEVEL_LIFECYCLE,
    get_system_log,
    reset_system_log_for_tests,
)


@pytest.mark.parametrize("mode_name", ["safe", "test"])
def test_for_mode_boots_phenotype(mode_name: str) -> None:
    reset_system_log_for_tests()
    expected = get_boot_mode(mode_name)
    host = ApplicationHost.for_mode(mode_name)
    assert host.boot_mode is not None
    assert host.boot_mode.name == mode_name
    assert host.composition.services == expected.composition.services
    assert host.composition.surfaces == ()
    assert host.composition.capabilities == frozenset()
    assert host.boot_mode.recover_on_start is False

    host.start()
    try:
        assert host.is_started
        walk = host.boot_walk
        assert walk is not None
        by_id = {row["phase"]: row for row in walk}
        assert by_id["host.ready"]["outcome"] == "ok"
        assert by_id["host.recover"]["outcome"] == "skip"
        assert by_id["host.recover"]["reason"] == "mode_recover_off"
        # Embedded: no surfaces. Projections omit is admission, not a boot skip.
        assert by_id["host.surfaces.mount"]["outcome"] == "skip"
        assert not host.admission.has_capability("projections")
        assert "host.projections.attach" not in by_id

        # Core product doors only (no assist/design/analytics chrome).
        assert host.system is not None
        assert host.session is not None
        assert host.definitions is not None
        assert host.execution is not None
        assert host.assist is None
        assert host.design is None
        assert host.analytics is None
        # Embedded DNA: drain never starts.
        plane = host.runtime().work_plane
        assert plane is None or plane.is_running is False

        boot = host.control_plane_status()["boot"]
        assert boot["mode"] == mode_name
        assert boot["membership"]["services"] == list(
            composition_profile_from_name("embedded").services
        )
        assert boot["membership"]["surfaces"] == []
        assert boot["last_walk"] is not None
        assert any(r["phase"] == "host.ready" for r in boot["last_walk"])
        assert boot["mode_detail"]["recover_on_start"] is False
        assert "allow_background_drain" not in boot["mode_detail"]
    finally:
        host.shutdown()


@pytest.mark.parametrize("mode_name", ["safe", "test"])
def test_mode_applies_system_log_level_defaults(mode_name: str) -> None:
    reset_system_log_for_tests()
    expected = get_boot_mode(mode_name)
    host = ApplicationHost.for_mode(mode_name)
    host.start()
    try:
        slog = get_system_log()
        assert slog.level == expected.system_log_level
        assert slog.level == LEVEL_LIFECYCLE
        if mode_name == "test":
            # test mode forces console off when env is unset
            assert slog.console is False
        # Mode name appears on host boot.start and host ready
        starts = [r for r in slog.recent() if r.event == "boot.start"]
        assert starts and starts[0].fields.get("mode") == mode_name
        host_ready = [
            r for r in slog.recent() if r.event == "ready" and r.fields.get("schedule") == "host"
        ]
        assert host_ready and host_ready[0].fields.get("mode") == mode_name
    finally:
        host.shutdown()


@pytest.mark.parametrize("mode_name", ["safe", "test"])
def test_spine_submit_flow_on_mode(mode_name: str) -> None:
    """Definition → pattern → job succeeds on declared green-bar modes."""
    reset_system_log_for_tests()
    host = ApplicationHost.for_mode(mode_name)
    host.start()
    try:
        job_id = f"mode-spine-{mode_name}"
        flow = FlowDefinition(
            name=f"mode-spine-{mode_name}",
            pattern="wizard",
            options={"steps": 1},
        )
        job = host.execute(SubmitFlowCommand(flow=flow, job_id=job_id))
        assert job.id == job_id
        assert job.status.value == "WAITING_FOR_INPUT"
        host.provide_input(job_id, "ok")
        # Re-read job after continue (spine: submit → wait → resume → done).
        job = host.runtime().orchestration.get_job(job_id)
        assert job is not None
        assert job.status.value == "SUCCEEDED"
    finally:
        host.shutdown()


def test_for_mode_accepts_boot_mode_instance() -> None:
    reset_system_log_for_tests()
    host = ApplicationHost.for_mode(BootMode.safe())
    assert host.boot_mode is not None
    assert host.boot_mode.name == "safe"
    host.start()
    try:
        assert host.is_started
    finally:
        host.shutdown()


def test_for_mode_unknown_raises() -> None:
    with pytest.raises(ValueError, match="Unknown boot mode"):
        ApplicationHost.for_mode("not-a-mode")


def test_boot_walk_none_before_start() -> None:
    host = ApplicationHost.for_mode("test")
    assert host.boot_walk is None
