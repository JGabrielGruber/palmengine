"""Characterization tests for residual host packaging status (T2 / 0.48 · CS-002).

0.48 pinned JSON shapes for the ``HostObservability`` extraction.
0.61.7 (CS-002): those bags are **host packaging residual**, not living-load
law. Tests assert packaging domain keys still exist (superset OK for demotion
markers) and that demotion stamps are present. Living eyes are
``inspect.top`` / ``inspect.vitality`` → ``palm.system.vitality``.

See docs/VISION-0.61.md · TECH-DEBT CS-002 · ADR-030 D9.
"""

from __future__ import annotations

from bundles.standard.app import ApplicationHost, DeploymentProfile
from bundles.standard.app.host.observability import EYES_LAW, PACKAGING_ROLE
from bundles.standard.app.settings import PalmSettings
from palm.common.events.consumers import DEFAULT_JOURNAL_CONSUMERS

# Domain keys (packaging residual). Demotion markers may also be present.
EVENT_PLANE_KEYS = {
    "orchestration_bus",
    "host_coordination_bus",
    "inbound_internal_bus",
    "work_drain_bus",
    "journal_bus",
    "internal_inbound_bindings",
    "orchestration_event_types",
    "system_log_level",  # 0.59.1a process narrative
    "system_log_recent",
    "note",
}

OPS_KEYS = {
    "invoke_route",
    "invoke_route_short",
    "storage_backend",
    "storage_durable",
    "event_log_durable",
    "event_log_note",
    "server_profile_hint",
}

CONTROL_PLANE_KEYS = {
    "work_pending",
    "start_plane_running",
    "work_dropped_depth",
    "schedules",
    "schedule_count",
    "outbox_pending",
    "journal",
    "journal_consumers",
    "inbound_bindings",
    "inbound_count",
    "boot",  # 0.59.2 phase tables + mode
    "event_plane",
    "ops",
}

DEMOTION_KEYS = {"role", "eyes_law", "operate_paths", "note"}


def _assert_packaging_demotion(bag: dict) -> None:
    assert bag["role"] == PACKAGING_ROLE
    assert bag["eyes_law"] == EYES_LAW
    assert "inspect/top" in bag["operate_paths"]
    assert isinstance(bag["note"], str) and "CS-002" in bag["note"]


def test_event_plane_status_full_contract(host: ApplicationHost) -> None:
    ep = host.event_plane_status()
    assert EVENT_PLANE_KEYS <= set(ep)
    assert DEMOTION_KEYS <= set(ep)
    _assert_packaging_demotion(ep)
    # Coordination stays on the host bus; journal rides the orchestration bus.
    assert ep["host_coordination_bus"] == "host"
    assert ep["journal_bus"] == ep["orchestration_bus"]
    assert ep["orchestration_event_types"] == [
        "job.completed",
        "flow.session.succeeded",
        "flow.session.failed",
    ]
    # Orchestration/inbound/work-drain share one bus id.
    assert ep["inbound_internal_bus"] == ep["orchestration_bus"]
    assert ep["work_drain_bus"] == ep["orchestration_bus"]
    assert ep["orchestration_bus"] in {"runtime", "host_fallback"}
    assert isinstance(ep["internal_inbound_bindings"], int)


def test_ops_status_full_contract(host: ApplicationHost) -> None:
    ops = host.ops_status()
    assert OPS_KEYS <= set(ops)
    assert DEMOTION_KEYS <= set(ops)
    _assert_packaging_demotion(ops)
    assert ops["invoke_route"] == "POST /v1/api/providers/{provider}/{resource_ref}/invoke"
    assert ops["invoke_route_short"] == "POST /v1/api/resources/{resource_ref}/invoke"
    assert isinstance(ops["storage_durable"], bool)
    # event_log_durable is tri-state (True/False/None); note only set when False.
    assert ops["event_log_durable"] in {True, False, None}
    if ops["event_log_durable"] is False:
        assert isinstance(ops["event_log_note"], str)


def test_control_plane_status_full_contract(host: ApplicationHost) -> None:
    cp = host.control_plane_status()
    assert CONTROL_PLANE_KEYS <= set(cp)
    assert DEMOTION_KEYS <= set(cp)
    _assert_packaging_demotion(cp)
    # Counts are consistent with their lists.
    assert cp["schedule_count"] == len(cp["schedules"])
    assert cp["inbound_count"] == len(cp["inbound_bindings"])
    assert cp["journal_consumers"] == list(DEFAULT_JOURNAL_CONSUMERS)
    assert "start_plane_running" in cp
    assert isinstance(cp["work_pending"], int)
    assert isinstance(cp["outbox_pending"], int)
    # Nested residual bags also demoted.
    assert EVENT_PLANE_KEYS <= set(cp["event_plane"])
    assert OPS_KEYS <= set(cp["ops"])
    _assert_packaging_demotion(cp["event_plane"])
    _assert_packaging_demotion(cp["ops"])


def test_status_reports_degrade_without_started_workplane() -> None:
    """Fallback branches: an unstarted host still returns well-formed packaging."""
    host = ApplicationHost(
        settings=PalmSettings.for_tests(load_examples=False),
        profile=DeploymentProfile.all_in_one(),
    )
    # No start() — start plane / inbound / journal are unset.
    ep = host.event_plane_status()
    assert EVENT_PLANE_KEYS <= set(ep)
    assert ep["orchestration_bus"] == "host_fallback"
    assert ep["internal_inbound_bindings"] == 0
    _assert_packaging_demotion(ep)

    cp = host.control_plane_status()
    assert CONTROL_PLANE_KEYS <= set(cp)
    assert cp["work_pending"] == 0
    assert cp["outbox_pending"] == 0
    assert cp["start_plane_running"] is False
    assert cp["schedules"] == []
    assert cp["inbound_bindings"] == []
    _assert_packaging_demotion(cp)

    ops = host.ops_status()
    assert OPS_KEYS <= set(ops)
    _assert_packaging_demotion(ops)
