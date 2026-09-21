"""0.59.1 — Boot inventory characterization (today's order + spine contracts).

Pins what ApplicationHost and BaseRuntime start do *now* so schedule migration
cannot drift silently. Not the future phase API — see docs/BOOT-INVENTORY.md.
"""

from __future__ import annotations

from typing import Any

import pytest

from palm.app import ApplicationHost, DeploymentProfile
from palm.app.bootstrap import ensure_plugins
from palm.app.settings import PalmSettings
from palm.runtimes.embedded import EmbeddedRuntime
from palm.system.subsystems.planes.session.plane import SessionPlaneService
from palm.system.subsystems.planes.wait.plane import WaitPlaneService

# Collaborator call order on collapsed all_in_one (server off).
# 0.59.5: surfaces.mount PhaseSkip before _start_server_surface when
# deployment.server is false — so that collaborator is not invoked.
HOST_START_PHASE_ORDER: tuple[str, ...] = (
    "kernel.bootstrap",
    "host.event",
    "system.spawn",
    "definitions.load",
    "product.wire",
    "recover",
)

# Full schedule seat ids (walker always visits; optional seats may skip).
# 0.68.1: empty host.projections.attach composted — DNA hand already attached.
HOST_WALK_PHASE_IDS: tuple[str, ...] = (
    "host.system_log",
    "host.kernel.bootstrap",
    "host.event",
    "host.workers.note",
    "host.system.spawn",
    "host.definitions.load",
    "host.product.wire",
    "host.surfaces.mount",
    "host.recover",
    "host.ready",
)


@pytest.fixture
def spine_settings() -> PalmSettings:
    """Minimal host settings for spine boot (memory, no examples)."""
    return PalmSettings.for_tests(load_examples=False)


def test_host_start_phase_order_all_in_one(spine_settings: PalmSettings) -> None:
    """ApplicationHost.start walks a fixed collaborator order (collapsed profile)."""
    host = ApplicationHost(
        settings=spine_settings,
        profile=DeploymentProfile.all_in_one(),
    )
    seen: list[str] = []

    real_bootstrap = host._app.bootstrap
    real_spawn = host._spawner.spawn_runtimes
    real_load = host._app.load_definitions
    real_wire = host._wire_cqrs
    real_surface = host._start_server_surface
    real_recover = host._recovery.recover

    def track(name: str, fn: Any) -> Any:
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            seen.append(name)
            return fn(*args, **kwargs)

        return wrapper

    host._app.bootstrap = track("kernel.bootstrap", real_bootstrap)  # type: ignore[method-assign]
    host._spawner.spawn_runtimes = track("system.spawn", real_spawn)  # type: ignore[method-assign]
    host._app.load_definitions = track("definitions.load", real_load)  # type: ignore[method-assign]
    host._wire_cqrs = track("product.wire", real_wire)  # type: ignore[method-assign]
    host._start_server_surface = track("surfaces.mount", real_surface)  # type: ignore[method-assign]
    host._recovery.recover = track("recover", real_recover)  # type: ignore[method-assign]

    orig_event_init = host._event.initialize

    def event_init_tracked() -> None:
        seen.append("host.event")
        return orig_event_init()

    host._event.initialize = event_init_tracked  # type: ignore[method-assign]

    try:
        host.start()
        assert host.is_started
        # Collaborators that actually ran (surfaces skipped on collapsed profile).
        core = [p for p in seen if p in HOST_START_PHASE_ORDER]
        assert core == list(HOST_START_PHASE_ORDER)
        assert "surfaces.mount" not in seen  # PhaseSkip before collaborator
        # Walker still visits every host seat (skip outcomes on optional phases).
        walked = [w.phase for w in (host._last_boot_walk or [])]
        assert walked == list(HOST_WALK_PHASE_IDS)
        by_id = {w.phase: w for w in (host._last_boot_walk or [])}
        assert by_id["host.surfaces.mount"].outcome == "skip"
        assert by_id["host.surfaces.mount"].reason == "deployment.server_off"
    finally:
        host.shutdown()


def test_spine_host_post_start_contracts(spine_settings: PalmSettings) -> None:
    """Collapsed host exposes product doors + system planes (spine green bar)."""
    host = ApplicationHost(
        settings=spine_settings,
        profile=DeploymentProfile.all_in_one(),
    )
    host.start()
    try:
        assert host.is_started
        assert host.running_runtimes() == ["main"]
        rt = host.runtime()
        assert isinstance(rt, EmbeddedRuntime)
        assert rt.is_started
        assert isinstance(rt.wait_plane, WaitPlaneService)
        assert isinstance(rt.session_plane, SessionPlaneService)
        # Product services built from composition (all_in_one services).
        assert host.system is not None
        assert host.session is not None
        assert host.definitions is not None
        assert host.execution is not None
        # Composition membership truth (0.59.5).
        assert "inspect" in host.composition.services
        assert "session" in host.composition.services
        assert host.admission.has_capability("projections")
        assert host.membership_snapshot()["services"]
    finally:
        host.shutdown()


def test_system_start_alone_attaches_planes(spine_settings: PalmSettings) -> None:
    """BaseRuntime system schedule without host still attaches wait + session."""
    from palm.app.bootstrap import runtime_start_options

    rt = EmbeddedRuntime()
    rt.start(**runtime_start_options(spine_settings))
    try:
        assert rt.is_started
        assert isinstance(rt.wait_plane, WaitPlaneService)
        assert isinstance(rt.session_plane, SessionPlaneService)
        # Execution port structural surface
        assert hasattr(rt, "execution")
        assert rt.storage.is_initialized
    finally:
        rt.stop()


def test_ensure_core_plugins_idempotent() -> None:
    """Plugin ensure may run host + system + tests; must be safe to repeat."""
    ensure_plugins()
    ensure_plugins()
    # Second call walks the same names. Import is idempotent.
    from palm.common.patterns._registry import registered_builders

    assert "wizard" in registered_builders()


def test_host_start_idempotent(spine_settings: PalmSettings) -> None:
    """Second host.start() is a no-op (does not re-spawn)."""
    host = ApplicationHost(
        settings=spine_settings,
        profile=DeploymentProfile.all_in_one(),
    )
    host.start()
    try:
        host.start()
        assert host.running_runtimes() == ["main"]
    finally:
        host.shutdown()


def test_composition_services_gate_build(spine_settings: PalmSettings) -> None:
    """build_all honors composition.services (membership truth)."""
    from palm.app.host.composition import composition_profile_from_name

    lean = composition_profile_from_name("embedded")
    host = ApplicationHost(
        settings=spine_settings,
        profile=DeploymentProfile.all_in_one(),
        composition=lean,
    )
    host.start()
    try:
        assert host.system is not None
        assert host.session is not None
        assert host.definitions is not None
        assert host.execution is not None
        # embedded CORE_SERVICES — no assist/design chrome
        assert host.assist is None
        assert host.design is None
        # 0.67.17: host.analytics is the install organ. Default all_in_one DNA
        # lists it; composition omit of AnalyticsService does not hide the organ.
        from palm.services.analytics import AnalyticsService

        assert host.analytics is host.runtime().install.analytics
        assert host.analytics is not None
        assert not isinstance(host.analytics, AnalyticsService)
    finally:
        host.shutdown()


def test_inventory_constants_match_documented_count() -> None:
    """Guard: collaborator order + full walk table stay aligned with inventory."""
    # Collaborators on collapsed profile (no surfaces.mount call).
    assert len(HOST_START_PHASE_ORDER) == 6
    assert HOST_START_PHASE_ORDER[0] == "kernel.bootstrap"
    assert HOST_START_PHASE_ORDER[-1] == "recover"
    assert "projections.attach" not in HOST_START_PHASE_ORDER
    assert len(HOST_WALK_PHASE_IDS) == 10
    assert HOST_WALK_PHASE_IDS[0] == "host.system_log"
    assert HOST_WALK_PHASE_IDS[-1] == "host.ready"
    assert "host.projections.attach" not in HOST_WALK_PHASE_IDS
