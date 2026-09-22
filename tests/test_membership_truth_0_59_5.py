"""0.59.5 — CompositionProfile is membership truth on the migrated path.

- Runtime gates read ``composition.has`` / ``composition.surfaces`` / services only.
- Deployment may *feed* the settings resolver (server work-drain → capability);
  it is not a second OR at phase time.
- Explicit composition wins over deployment.
- Phase skips use ``composition_off:*`` / mode reasons visible in SystemLog.
"""

from __future__ import annotations

from dataclasses import replace

from bundles.standard.app.bootstrap import composition_profile_from_settings
from bundles.standard.app.host.application_host import ApplicationHost
from bundles.standard.app.host.composition import composition_profile_from_name
from bundles.standard.app.host.roles import DeploymentProfile
from bundles.standard.app.settings import PalmSettings
from palm.core.structure import CAPABILITY_WORK_DRAIN
from palm.system.log import get_system_log, reset_system_log_for_tests


def test_settings_resolver_does_not_write_work_drain() -> None:
    """Flag and deployment do not write work_drain onto composition."""
    settings = PalmSettings.for_tests(load_examples=False)
    bare = composition_profile_from_settings(settings)
    assert "work_drain" not in bare.capabilities

    with_server = composition_profile_from_settings(
        settings, deployment=DeploymentProfile.server_only(port=0)
    )
    assert "work_drain" not in with_server.capabilities


def test_server_profile_host_gains_work_drain_membership() -> None:
    """Host with server deployment + settings path has work_drain on composition."""
    settings = PalmSettings.for_tests(load_examples=False)
    host = ApplicationHost(
        settings=settings,
        profile=DeploymentProfile.server_only(port=0),
    )
    assert not host.composition.has("work_drain")
    host.start()
    try:
        plane = host.runtime().work_plane
        assert plane is not None
        assert plane.is_running is True
    finally:
        host.shutdown()


def test_explicit_composition_does_not_veto_dna_work_drain() -> None:
    """Empty composition is not a peer king; server DNA lists work_drain."""
    settings = PalmSettings.for_tests(load_examples=False)
    host = ApplicationHost(
        settings=settings,
        profile=DeploymentProfile.server_only(port=0),
        composition=replace(composition_profile_from_name("all_in_one"), capabilities=frozenset()),
    )
    assert not host.composition.has("work_drain")
    host.start()
    try:
        rt = host.runtime()
        assert CAPABILITY_WORK_DRAIN in rt.structure.materialized_capabilities
        assert "work_drain" in rt.supervisor.names()
        plane = host.runtime().work_plane
        assert plane is not None
        assert plane.is_running is True
    finally:
        host.shutdown()


def test_work_drain_gate_is_dna_not_composition_or() -> None:
    """all_in_one DNA lists work_drain; composition empty and flags are not kings."""
    settings = PalmSettings.for_tests(load_examples=False)
    host = ApplicationHost(
        settings=settings,
        profile=DeploymentProfile.all_in_one(),
        composition=replace(composition_profile_from_name("all_in_one"), capabilities=frozenset()),
    )
    host.start()
    try:
        assert not host.composition.has("work_drain")
        rt = host.runtime()
        assert CAPABILITY_WORK_DRAIN in rt.structure.materialized_capabilities
        assert "work_drain" in rt.supervisor.names()
        plane = rt.work_plane
        assert plane is not None
        assert plane.is_running is True
    finally:
        host.shutdown()


def test_work_drain_follows_definition_not_composition() -> None:
    """all_in_one DNA lists work_drain; composition does not own membership."""
    settings = PalmSettings.for_tests(load_examples=False)
    host = ApplicationHost(
        settings=settings,
        profile=DeploymentProfile.all_in_one(),
        composition=replace(composition_profile_from_name("all_in_one"), capabilities=frozenset()),
    )
    host.start()
    try:
        assert not host.composition.has("work_drain")
        rt = host.runtime()
        definition = rt.structure.definition
        assert definition is not None
        assert definition.has_capability(CAPABILITY_WORK_DRAIN)
        assert CAPABILITY_WORK_DRAIN in rt.structure.materialized_capabilities
        assert "work_drain" in rt.supervisor.names()
        plane = rt.work_plane
        assert plane is not None
        assert plane.is_running is True
    finally:
        host.shutdown()


def test_surfaces_skip_when_composition_has_none() -> None:
    """Server deployment + empty surfaces → composition_off:surfaces, not silent mount."""
    settings = PalmSettings.for_tests(load_examples=False)
    host = ApplicationHost(
        settings=settings,
        profile=DeploymentProfile.server_only(port=0),
        composition=replace(
            composition_profile_from_name("server"),
            surfaces=(),
            capabilities=frozenset({"projections", "journal"}),
        ),
    )
    host.start()
    try:
        by_id = {w.phase: w for w in (host._last_boot_walk or [])}
        assert by_id["host.surfaces.mount"].outcome == "skip"
        assert by_id["host.surfaces.mount"].reason == "composition_off:surfaces"
    finally:
        host.shutdown()


def test_projections_omit_is_admission_not_a_boot_phase() -> None:
    """0.68.1: DNA omit is admission. Empty host.projections.attach is gone."""
    settings = PalmSettings.for_tests(load_examples=False)
    host = ApplicationHost(
        settings=settings,
        composition=replace(composition_profile_from_name("all_in_one"), capabilities=frozenset()),
    )
    host.start(structure_definition_id="local.embedded")
    try:
        assert not host.admission.has_capability("projections")
        walked = [w.phase for w in (host._last_boot_walk or [])]
        assert "host.projections.attach" not in walked
    finally:
        host.shutdown()


def test_boot_mode_test_skips_background_with_mode_reason() -> None:
    reset_system_log_for_tests()
    settings = PalmSettings.for_tests(load_examples=False)
    # test mode composition is embedded (no work_drain) + mode forbids background
    host = ApplicationHost(settings=settings, boot_mode="test")
    host.start()
    try:
        plane = host.runtime().work_plane
        assert plane is None or plane.is_running is False
        rt = host.runtime()
        assert rt.supervisor is None or "work_drain" not in rt.supervisor.names()
        boot = host.control_plane_status()["boot"]
        assert boot["membership"]["services"]
        assert "capabilities" in boot["membership"]
    finally:
        host.shutdown()


def test_system_log_boot_start_carries_membership() -> None:
    """Lifecycle boot.start lists services/surfaces/capabilities (phenotype visible)."""
    reset_system_log_for_tests()
    settings = PalmSettings.for_tests(load_examples=False)
    host = ApplicationHost(
        settings=settings,
        profile=DeploymentProfile.all_in_one(),
    )
    host.start()
    try:
        slog = get_system_log()
        starts = [r for r in slog.recent() if r.event == "boot.start"]
        assert starts
        fields = starts[0].fields
        assert "inspect" in str(fields.get("services", ""))
        assert "capabilities" in fields
        assert host.membership_snapshot()["services"]
    finally:
        host.shutdown()


def test_membership_snapshot_matches_composition() -> None:
    host = ApplicationHost(
        settings=PalmSettings.for_tests(load_examples=False),
        composition=composition_profile_from_name("embedded"),
    )
    snap = host.membership_snapshot()
    assert snap["services"] == list(composition_profile_from_name("embedded").services)
    assert snap["surfaces"] == []
    assert snap["capabilities"] == []
