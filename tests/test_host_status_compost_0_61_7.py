"""0.61.7 / CS-002 — host status demoted to packaging residual."""

from __future__ import annotations

import json

from bundles.standard.app.host.application_host import ApplicationHost
from bundles.standard.app.host.observability import EYES_LAW, PACKAGING_ROLE
from bundles.standard.app.host.roles import DeploymentProfile
from bundles.standard.app.settings import PalmSettings
from palm.system.log import reset_system_log_for_tests
from palm.system.vitality import VITALITY_SNAPSHOT_SCHEMA


def _started_host() -> ApplicationHost:
    reset_system_log_for_tests()
    host = ApplicationHost(
        settings=PalmSettings.for_tests(load_examples=False),
        profile=DeploymentProfile.all_in_one(),
        boot_mode="test",
    )
    host.start()
    return host


def test_packaging_status_is_demoted_control_plane() -> None:
    host = _started_host()
    try:
        pkg = host.packaging_status()
        cp = host.control_plane_status()
        assert pkg["role"] == PACKAGING_ROLE
        assert pkg["eyes_law"] == EYES_LAW
        assert "inspect/top" in pkg["operate_paths"]
        assert "CS-002" in pkg["note"]
        # Same residual body as control_plane_status (single bag).
        assert pkg["work_pending"] == cp["work_pending"]
        assert pkg["start_plane_running"] == cp["start_plane_running"]
        assert pkg["boot"]["mode"] == cp["boot"]["mode"]
        # Nested residual still demoted.
        assert pkg["event_plane"]["role"] == PACKAGING_ROLE
        assert pkg["ops"]["role"] == PACKAGING_ROLE
    finally:
        host.shutdown()


def test_host_status_is_not_living_seat_law() -> None:
    """Packaging bags must not invent seat summary as if they were vitality."""
    host = _started_host()
    try:
        for bag in (
            host.packaging_status(),
            host.event_plane_status(),
            host.ops_status(),
            host.control_plane_status(),
        ):
            assert "present_ids" not in bag
            assert "seats" not in bag
            assert "fragments" not in bag
            assert bag["eyes_law"] == EYES_LAW
        # Living eyes remain inspect → projection.
        top = host.inspect.top(host.runtime())
        assert top["schema"] == VITALITY_SNAPSHOT_SCHEMA
        assert top["source"] == "palm.system.vitality"
        assert "present_ids" in top["summary"]
    finally:
        host.shutdown()


def test_doctor_control_plane_is_host_packaging() -> None:
    host = _started_host()
    try:
        report = host.inspect.doctor(host.runtime())
        cp = report["control_plane"]
        assert cp.get("role") == PACKAGING_ROLE or report["role"] == "anatomy_packaging"
        # Eyes still from projection, not host status.
        assert report["top"]["source"] == "palm.system.vitality"
        assert report["kind"] == "legacy_doctor"
        if isinstance(cp, dict) and "eyes_law" in cp:
            assert cp["eyes_law"] == EYES_LAW
        json.dumps(report)
    finally:
        host.shutdown()
