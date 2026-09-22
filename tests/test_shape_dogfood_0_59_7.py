"""0.59.7 — Full modes + shape presets dogfood in CI.

Green bar for this slice:
- ``dev`` / ``prod`` and shape presets boot via :meth:`ApplicationHost.for_mode`
  (no private host internals).
- Membership + deployment roles match the named :class:`BootMode`.
- Walk outcomes match phenotype (surfaces / recover / work_drain / projections).
- Spine SUCCEEDED on collapsed full modes (inline scheduler).
- Queued shapes (worker / server / prod) accept submit without pretending
  inline continue (honest residual for daemon/server schedulers).
"""

from __future__ import annotations

import pytest

from bundles.standard.app.host.application_host import ApplicationHost
from bundles.standard.app.host.boot.modes import BootMode, get_boot_mode, list_boot_modes
from bundles.standard.app.settings import PalmSettings
from palm.common.cqrs.command import SubmitFlowCommand
from palm.definitions.flow import FlowDefinition
from palm.system.log import get_system_log, reset_system_log_for_tests

# Modes with collapsed master+worker, no HTTP — spine runs inline.
_COLLAPSED_FULL = ("dev", "cli", "mcp", "all_in_one")
# Network / worker shapes — boot + membership; submit may stay PENDING on queue.
_QUEUED_SHAPES = ("worker", "server", "prod")
_ALL_SHAPES = _COLLAPSED_FULL + _QUEUED_SHAPES


def _settings() -> PalmSettings:
    return PalmSettings.for_tests(load_examples=False)


def _host_for(mode_name: str) -> ApplicationHost:
    """CI-safe host for a named mode (ephemeral port for server deployments)."""
    expected = get_boot_mode(mode_name)
    kwargs: dict = {"settings": _settings()}
    if expected.deployment.server:
        kwargs["server_port"] = 0
    return ApplicationHost.for_mode(mode_name, **kwargs)


def test_all_named_modes_are_registered() -> None:
    names = set(list_boot_modes())
    for required in (
        "safe",
        "test",
        "dev",
        "prod",
        "cli",
        "mcp",
        "worker",
        "server",
        "all_in_one",
    ):
        assert required in names


@pytest.mark.parametrize("mode_name", list(_ALL_SHAPES))
def test_shape_boots_phenotype(mode_name: str) -> None:
    reset_system_log_for_tests()
    expected = get_boot_mode(mode_name)
    host = _host_for(mode_name)
    assert host.boot_mode is not None
    assert host.boot_mode.name == mode_name
    assert host.composition.services == expected.composition.services
    assert host.composition.surfaces == expected.composition.surfaces
    assert host.composition.capabilities == expected.composition.capabilities
    assert host.boot_mode.recover_on_start is True
    if expected.deployment.server:
        assert host.profile.server is True
        assert host.profile.server_port == 0

    host.start()
    try:
        assert host.is_started
        walk = host.boot_walk
        assert walk is not None
        by_id = {row["phase"]: row for row in walk}
        assert by_id["host.ready"]["outcome"] == "ok"
        assert by_id["host.recover"]["outcome"] == "ok"

        # Surfaces: composition *what* × deployment *where*.
        if expected.deployment.server and expected.composition.surfaces:
            assert by_id["host.surfaces.mount"]["outcome"] == "ok"
        elif not expected.deployment.server:
            assert by_id["host.surfaces.mount"]["outcome"] == "skip"
            assert by_id["host.surfaces.mount"]["reason"] == "deployment.server_off"
        else:
            assert by_id["host.surfaces.mount"]["outcome"] == "skip"
            assert by_id["host.surfaces.mount"]["reason"] == "composition_off:surfaces"

        # Projections capability is DNA, not a host boot phase (0.68.1).
        assert "host.projections.attach" not in by_id

        # Background work drain: DNA capabilities list (not composition.has).
        rt = host.runtime()
        if rt.structure is not None and "work_drain" in rt.structure.materialized_capabilities:
            plane = rt.work_plane
            assert plane is not None
            assert plane.is_running is True
        else:
            plane = rt.work_plane
            assert plane is None or plane.is_running is False

        # Declared services must exist; chrome outside the dep closure must not.
        # Note: ``build_all(only=…)`` also builds transitive deps (worker asks for
        # ``execution`` and still gets system/session/definitions).
        for name in expected.composition.services:
            assert getattr(host, name, None) is not None, f"missing service {name}"
        for chrome in ("assist", "design", "analytics"):
            if chrome not in expected.composition.services:
                assert getattr(host, chrome, None) is None, f"unexpected chrome {chrome}"

        boot = host.control_plane_status()["boot"]
        assert boot["mode"] == mode_name
        assert boot["membership"]["services"] == list(expected.composition.services)
        assert boot["membership"]["surfaces"] == list(expected.composition.surfaces)
        assert boot["last_walk"] is not None
        assert boot["mode_detail"]["recover_on_start"] is True
        assert "allow_background_drain" not in boot["mode_detail"]
    finally:
        host.shutdown()


@pytest.mark.parametrize("mode_name", ["dev", "prod"])
def test_dev_prod_system_log_levels(mode_name: str) -> None:
    reset_system_log_for_tests()
    expected = get_boot_mode(mode_name)
    host = _host_for(mode_name)
    host.start()
    try:
        slog = get_system_log()
        assert slog.level == expected.system_log_level
        starts = [r for r in slog.recent() if r.event == "boot.start"]
        assert starts and starts[0].fields.get("mode") == mode_name
    finally:
        host.shutdown()


@pytest.mark.parametrize("mode_name", list(_COLLAPSED_FULL))
def test_spine_succeeded_on_collapsed_full_modes(mode_name: str) -> None:
    """Inline collapsed hosts: submit → wait → continue → SUCCEEDED."""
    reset_system_log_for_tests()
    host = _host_for(mode_name)
    host.start()
    try:
        job_id = f"shape-spine-{mode_name}"
        flow = FlowDefinition(
            name=job_id,
            pattern="wizard",
            options={"steps": 1},
        )
        job = host.execute(SubmitFlowCommand(flow=flow, job_id=job_id))
        assert job.id == job_id
        assert job.status.value == "WAITING_FOR_INPUT"
        host.provide_input(job_id, "ok")
        job = host.runtime().orchestration.get_job(job_id)
        assert job is not None
        assert job.status.value == "SUCCEEDED"
    finally:
        host.shutdown()


@pytest.mark.parametrize("mode_name", list(_QUEUED_SHAPES))
def test_queued_shapes_accept_submit(mode_name: str) -> None:
    """Worker/server/prod use queued schedulers — submit is accepted; no fake inline SUCCEEDED."""
    reset_system_log_for_tests()
    host = _host_for(mode_name)
    host.start()
    try:
        job_id = f"shape-queue-{mode_name}"
        flow = FlowDefinition(
            name=job_id,
            pattern="wizard",
            options={"steps": 1},
        )
        job = host.execute(SubmitFlowCommand(flow=flow, job_id=job_id))
        assert job.id == job_id
        # Queued path may leave PENDING until a worker drains; do not require SUCCEEDED.
        assert job.status.value in {
            "PENDING",
            "RUNNING",
            "WAITING_FOR_INPUT",
            "SUCCEEDED",
        }
    finally:
        host.shutdown()


def test_for_mode_server_port_requires_server_deployment() -> None:
    with pytest.raises(ValueError, match="server_port requires a server deployment"):
        ApplicationHost.for_mode(
            "cli",
            settings=_settings(),
            server_port=0,
        )


def test_for_mode_accepts_dev_instance() -> None:
    reset_system_log_for_tests()
    host = ApplicationHost.for_mode(BootMode.dev(), settings=_settings())
    assert host.boot_mode is not None
    assert host.boot_mode.name == "dev"
    host.start()
    try:
        assert host.is_started
        assert host.assist is not None
    finally:
        host.shutdown()
