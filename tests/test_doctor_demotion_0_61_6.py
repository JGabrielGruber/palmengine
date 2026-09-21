"""0.61.6 / OD-001 — doctor demoted to anatomy packaging; eyes = top/vitality."""

from __future__ import annotations

from palm.app.host.application_host import ApplicationHost
from palm.app.host.composition import composition_profile_from_name
from palm.app.host.roles import DeploymentProfile
from palm.app.settings import PalmSettings
from palm.kits.server.diagnostics import build_doctor_report
from palm.runtimes.mcp.assist.operator import dispatch_operator_path
from palm.services.inspect.present import (
    DOCTOR_KIND,
    DOCTOR_ROLE,
    SOURCE_VITALITY,
    present_doctor,
)
from palm.system.log import reset_system_log_for_tests
from palm.system.vitality import VITALITY_SNAPSHOT_SCHEMA


def _started_host(*, with_assist: bool = False) -> ApplicationHost:
    reset_system_log_for_tests()
    if with_assist:
        host = ApplicationHost(
            settings=PalmSettings.for_tests(load_examples=False),
            profile=DeploymentProfile.all_in_one(),
            composition=composition_profile_from_name("all_in_one"),
        )
    else:
        host = ApplicationHost(
            settings=PalmSettings.for_tests(load_examples=False),
            profile=DeploymentProfile.all_in_one(),
            boot_mode="test",
        )
    host.start()
    return host


def test_doctor_envelope_is_demoted_anatomy() -> None:
    host = _started_host()
    try:
        report = host.inspect.doctor(host.runtime())
        assert report["kind"] == DOCTOR_KIND
        assert report["role"] == DOCTOR_ROLE
        assert report["eyes_law"] == SOURCE_VITALITY
        assert "inspect/top" in report["operate_paths"]
        assert "assist/vitality" in report["operate_paths"]
        assert "note" in report
        # Living eyes nested from projection.
        assert report["top"]["source"] == SOURCE_VITALITY
        assert report["top"]["schema"] == VITALITY_SNAPSHOT_SCHEMA
        assert report["vitality"]["source"] == SOURCE_VITALITY
        assert "summary" in report["vitality"]
        # Nested anatomy bag + flat compat packaging.
        assert "anatomy" in report
        assert report["anatomy"]["storage"] == report["storage"]
        assert "jobs" in report
        assert "status" in report
        assert "registries" in report
    finally:
        host.shutdown()


def test_doctor_does_not_own_seat_summary() -> None:
    """Seat presence lives under top (projection), not anatomy inventing seats."""
    host = _started_host()
    try:
        report = host.inspect.doctor(host.runtime())
        anatomy = report["anatomy"]
        assert "present_ids" not in anatomy
        assert "seats" not in anatomy
        assert "fragments" not in anatomy
        # Living seat summary is under top only.
        assert "present_ids" in report["top"]["summary"]
    finally:
        host.shutdown()


def test_build_doctor_report_is_anatomy_only() -> None:
    host = _started_host()
    try:
        rt = host.runtime()
        anatomy = build_doctor_report(rt)
        assert anatomy["role"] == DOCTOR_ROLE
        assert "storage" in anatomy
        assert "top" not in anatomy
        assert "seats" not in anatomy
        assert "present_ids" not in anatomy
    finally:
        host.shutdown()


def test_present_doctor_pure_helper() -> None:
    anatomy = {
        "role": DOCTOR_ROLE,
        "status": "ok",
        "storage": {"backend": "memory", "open": True},
        "jobs": {"total": 0},
        "issues": [],
    }
    top = {
        "schema": VITALITY_SNAPSHOT_SCHEMA,
        "source": SOURCE_VITALITY,
        "summary": {"present_ids": ["install"], "present_count": 1},
    }
    report = present_doctor(anatomy, top=top)
    assert report["kind"] == DOCTOR_KIND
    assert report["top"] is top
    assert report["anatomy"]["storage"]["backend"] == "memory"
    assert report["storage"]["backend"] == "memory"


def test_assist_doctor_carries_demotion_markers() -> None:
    host = _started_host(with_assist=True)
    try:
        assert host.assist is not None
        report = host.assist.doctor()
        assert report["kind"] == DOCTOR_KIND
        assert report["eyes_law"] == SOURCE_VITALITY
        via_path = host.assist.dispatch(["assist", "doctor"], {})
        assert via_path["kind"] == DOCTOR_KIND
        assert via_path["top"]["source"] == SOURCE_VITALITY
    finally:
        host.shutdown()


def test_operator_system_doctor_demoted() -> None:
    host = _started_host()
    try:
        via_system = dispatch_operator_path(host, ["system", "doctor"], {})
        via_inspect = dispatch_operator_path(host, ["inspect", "doctor"], {})
        assert via_system["kind"] == DOCTOR_KIND
        assert via_inspect["kind"] == DOCTOR_KIND
        assert via_system["eyes_law"] == SOURCE_VITALITY
        assert via_inspect["top"]["schema"] == VITALITY_SNAPSHOT_SCHEMA
    finally:
        host.shutdown()
