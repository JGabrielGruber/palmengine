"""0.44.1 — server host profile enables background work drain by default."""

from __future__ import annotations

from bundles.standard.app import ApplicationHost, PalmSettings
from bundles.standard.app.host.roles import DeploymentProfile
from palm.core.structure import CAPABILITY_WORK_DRAIN


def test_server_profile_starts_work_drain_without_env() -> None:
    """Server DNA lists work_drain; settings flag is not required to start it."""
    settings = PalmSettings(
        load_example_definitions=False,
        storage_backend="memory",
        rebuild_projections_on_startup=False,
        reconcile_instances_on_startup=False,
    )
    host = ApplicationHost(
        settings=settings,
        profile=DeploymentProfile.server_only(port=0),
    )
    host.start()
    try:
        assert host.admission.definition_id == "local.server"
        rt = host.runtime()
        assert CAPABILITY_WORK_DRAIN in rt.structure.materialized_capabilities
        assert "work_drain" in rt.supervisor.names()
        plane = host.runtime().work_plane
        assert plane is not None
        assert plane.is_running is True
    finally:
        host.shutdown()


def test_all_in_one_profile_starts_drain_from_dna() -> None:
    """all_in_one DNA lists work_drain; settings flag / composition are not kings."""
    settings = PalmSettings.for_tests(load_examples=False)
    host = ApplicationHost(
        settings=settings,
        profile=DeploymentProfile.all_in_one(),
    )
    host.start()
    try:
        assert host.admission.definition_id == "local.all_in_one"
        rt = host.runtime()
        assert CAPABILITY_WORK_DRAIN in rt.structure.materialized_capabilities
        assert "work_drain" in rt.supervisor.names()
        plane = host.runtime().work_plane
        assert plane is not None
        assert plane.is_running is True
    finally:
        host.shutdown()