"""0.68.1 — empty host.projections.attach composted."""

from __future__ import annotations

from bundles.standard.app.host.application_host import ApplicationHost
from bundles.standard.app.host.roles import DeploymentProfile
from bundles.standard.app.settings import PalmSettings
from palm.system.boot import HOST_PHASES, host_phase_ids


def test_host_phase_table_drops_projections_attach() -> None:
    assert "host.projections.attach" not in host_phase_ids()
    assert all(p.id != "host.projections.attach" for p in HOST_PHASES)


def test_unread_host_projection_builders_are_gone() -> None:
    import bundles.standard.app.host.wiring as wiring

    assert not hasattr(wiring, "build_host_projections")
    assert not hasattr(wiring, "register_host_projections")
    assert not hasattr(wiring, "HostProjections")


def test_cli_walk_has_no_projections_attach_phase() -> None:
    host = ApplicationHost(
        settings=PalmSettings.for_tests(load_examples=False),
        profile=DeploymentProfile.all_in_one(),
    )
    host.start()
    try:
        assert host.admission.has_capability("projections")
        walked = [w.phase for w in (host._last_boot_walk or [])]
        assert "host.projections.attach" not in walked
        assert walked == list(host_phase_ids())
    finally:
        host.shutdown()
