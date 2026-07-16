"""Characterization tests for the three ApplicationHost status reports (T2 / 0.48.0).

These pin the *complete* JSON shape and stable literal values of
``event_plane_status`` / ``ops_status`` / ``control_plane_status`` so the
0.48 ``HostObservability`` extraction (seam 3) is provably behavior-preserving.
They assert the full key set — not just a scenario key — and exercise the
degrade-to-fallback branches. If a later refactor changes a key, that is a
contract change and must be intentional (and mirrored here).

See docs/VISION-0.48.md and docs/adr/018-application-host-decomposition.md.
"""

from __future__ import annotations

from palm.app import ApplicationHost, DeploymentProfile
from palm.app.settings import PalmSettings
from palm.common.events.consumers import DEFAULT_JOURNAL_CONSUMERS

EVENT_PLANE_KEYS = {
    "orchestration_bus",
    "host_coordination_bus",
    "inbound_internal_bus",
    "work_drain_bus",
    "journal_bus",
    "internal_inbound_bindings",
    "orchestration_event_types",
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
    "work_drain_running",
    "work_drain_background",
    "work_dropped_depth",
    "schedules",
    "schedule_count",
    "outbox_pending",
    "journal",
    "journal_consumers",
    "inbound_bindings",
    "inbound_count",
    "event_plane",
    "ops",
}


def test_event_plane_status_full_contract(host: ApplicationHost) -> None:
    ep = host.event_plane_status()
    assert set(ep) == EVENT_PLANE_KEYS
    # Stable literals — coordination/journal always ride the host bus.
    assert ep["host_coordination_bus"] == "host"
    assert ep["journal_bus"] == "host"
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
    assert isinstance(ep["note"], str) and ep["note"]


def test_ops_status_full_contract(host: ApplicationHost) -> None:
    ops = host.ops_status()
    assert set(ops) == OPS_KEYS
    assert ops["invoke_route"] == "POST /v1/api/providers/{provider}/{resource_ref}/invoke"
    assert ops["invoke_route_short"] == "POST /v1/api/resources/{resource_ref}/invoke"
    assert isinstance(ops["storage_durable"], bool)
    # event_log_durable is tri-state (True/False/None); note only set when False.
    assert ops["event_log_durable"] in {True, False, None}
    if ops["event_log_durable"] is False:
        assert isinstance(ops["event_log_note"], str)


def test_control_plane_status_full_contract(host: ApplicationHost) -> None:
    cp = host.control_plane_status()
    assert set(cp) == CONTROL_PLANE_KEYS
    # Counts are consistent with their lists.
    assert cp["schedule_count"] == len(cp["schedules"])
    assert cp["inbound_count"] == len(cp["inbound_bindings"])
    assert cp["journal_consumers"] == list(DEFAULT_JOURNAL_CONSUMERS)
    # work_drain_background is a live alias of work_drain_running (dropped in 0.48.1?).
    assert cp["work_drain_background"] == cp["work_drain_running"]
    assert isinstance(cp["work_pending"], int)
    assert isinstance(cp["outbox_pending"], int)
    # Composition: control-plane nests the other two reports verbatim in shape.
    assert set(cp["event_plane"]) == EVENT_PLANE_KEYS
    assert set(cp["ops"]) == OPS_KEYS


def test_status_reports_degrade_without_started_workplane() -> None:
    """Fallback branches: an unstarted host still returns well-formed reports.

    Pins the ``except Exception``/``is None`` degrade paths that seams 3-5 move.
    """
    host = ApplicationHost(
        settings=PalmSettings.for_tests(load_examples=False),
        profile=DeploymentProfile.all_in_one(),
    )
    # No start() — _work_drain / _inbound / _event_journal are None.
    ep = host.event_plane_status()
    assert set(ep) == EVENT_PLANE_KEYS
    assert ep["orchestration_bus"] == "host_fallback"
    assert ep["internal_inbound_bindings"] == 0

    cp = host.control_plane_status()
    assert set(cp) == CONTROL_PLANE_KEYS
    assert cp["work_pending"] == 0
    assert cp["outbox_pending"] == 0
    assert cp["work_drain_running"] is False
    assert cp["schedules"] == []
    assert cp["inbound_bindings"] == []

    ops = host.ops_status()
    assert set(ops) == OPS_KEYS
