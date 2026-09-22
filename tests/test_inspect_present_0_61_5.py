"""0.61.5 — Inspect presents top/vitality from system projection only."""

from __future__ import annotations

from bundles.standard.app.host.application_host import ApplicationHost
from bundles.standard.app.host.composition import composition_profile_from_name
from bundles.standard.app.host.roles import DeploymentProfile
from bundles.standard.app.settings import PalmSettings
from bundles.standard.runtimes.mcp.assist.operator import dispatch_operator_path
from palm.services.inspect import InspectService, present_top
from palm.system.log import reset_system_log_for_tests
from palm.system.vitality import (
    SEAT_INSTALL,
    SEAT_WAIT_PLANE,
    VITALITY_SNAPSHOT_SCHEMA,
    project_top,
)


def _started_host(*, with_assist: bool = False) -> ApplicationHost:
    """Lean test phenotype by default; full services when assist door is under test."""
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


def test_inspect_top_matches_system_project_top() -> None:
    host = _started_host()
    try:
        rt = host.runtime()
        assert host.inspect is not None
        top = host.inspect.top(rt)
        sys_top = project_top(rt)
        # Product may add source; core fields match projection.
        assert top["schema"] == sys_top["schema"] == VITALITY_SNAPSHOT_SCHEMA
        assert top["summary"]["present_ids"] == sys_top["summary"]["present_ids"]
        assert top["source"] == "palm.system.vitality"
        assert SEAT_WAIT_PLANE in top["summary"]["present_ids"]
        assert SEAT_INSTALL in top["summary"]["present_ids"]
    finally:
        host.shutdown()


def test_inspect_vitality_is_full_snapshot() -> None:
    host = _started_host()
    try:
        body = host.inspect.vitality(host.runtime())
        assert body["schema"] == VITALITY_SNAPSHOT_SCHEMA
        assert body["source"] == "palm.system.vitality"
        assert "fragments" in body
        assert "seats" in body
        assert body["summary"]["present_count"] >= 1
    finally:
        host.shutdown()


def test_doctor_nests_projection_top() -> None:
    host = _started_host()
    try:
        report = host.inspect.doctor(host.runtime())
        assert "top" in report
        assert report["top"]["source"] == "palm.system.vitality"
        assert "summary" in report["top"]
        assert report["vitality"]["source"] == "palm.system.vitality"
        assert "note" in report["vitality"]
        # Demoted envelope (0.61.6 / OD-001) + anatomy packaging residual.
        assert report.get("kind") == "legacy_doctor"
        assert report.get("role") == "anatomy_packaging"
        assert "status" in report
        assert "jobs" in report
    finally:
        host.shutdown()


def test_operator_paths_system_and_inspect_top() -> None:
    host = _started_host()
    try:
        via_system = dispatch_operator_path(host, ["system", "top"], {})
        via_inspect = dispatch_operator_path(host, ["inspect", "top"], {})
        assert via_system["summary"]["present_ids"] == via_inspect["summary"]["present_ids"]
        via_vitality = dispatch_operator_path(host, ["inspect", "vitality"], {})
        assert via_vitality["schema"] == VITALITY_SNAPSHOT_SCHEMA
    finally:
        host.shutdown()


def test_assist_top_delegates_to_inspect() -> None:
    host = _started_host(with_assist=True)
    try:
        assert host.assist is not None
        top = host.assist.top()
        assert top["source"] == "palm.system.vitality"
        assert SEAT_INSTALL in top["summary"]["present_ids"]
        via_path = host.assist.dispatch(["assist", "top"], {})
        assert via_path["summary"]["present_ids"] == top["summary"]["present_ids"]
    finally:
        host.shutdown()


def test_present_top_module_is_projection_only() -> None:
    host = _started_host()
    try:
        rt = host.runtime()
        presented = present_top(rt)
        raw = project_top(rt)
        assert presented["summary"] == raw["summary"]
        assert presented["seats"] == raw["seats"]
        assert isinstance(host.inspect, InspectService)
    finally:
        host.shutdown()
