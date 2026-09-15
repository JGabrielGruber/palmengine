"""0.61.2 — VitalityRegistry + VitalityProjection (seat_walk fold)."""

from __future__ import annotations

from typing import Any

from palm.system.log import reset_system_log_for_tests
from palm.system.runtime.base import BaseRuntime
from palm.system.vitality import (
    CAPABILITY_EMISSION_WINDOW,
    CAPABILITY_LOADED_BULK,
    CAPABILITY_MONITOR_AGENT,
    CAPABILITY_PROCESS_RESOURCES,
    CAPABILITY_SEAT_WALK,
    LINEAGE_SAMPLED,
    MATURITY_INSTALLED,
    MATURITY_INTENTION,
    SEAT_WAIT_PLANE,
    STATE_ABSENT,
    STATE_OK,
    STATE_SKIPPED,
    VITALITY_SNAPSHOT_SCHEMA,
    CapabilityFragment,
    ProjectionOptions,
    SampleContext,
    VitalityCapability,
    VitalityProjection,
    VitalityRegistry,
    default_vitality_registry,
    discover_seats,
    project,
    project_seat_walk_only,
    project_top,
    reset_default_vitality_registry_for_tests,
)


def setup_function() -> None:
    reset_default_vitality_registry_for_tests()
    reset_system_log_for_tests()


# ── registry ─────────────────────────────────────────────────────────────────


def test_default_registry_has_seat_walk_enabled() -> None:
    reg = default_vitality_registry()
    assert CAPABILITY_SEAT_WALK in reg
    assert reg.is_enabled(CAPABILITY_SEAT_WALK)
    assert CAPABILITY_EMISSION_WINDOW in reg
    assert reg.is_enabled(CAPABILITY_EMISSION_WINDOW)
    row = next(r for r in reg.catalog() if r["id"] == CAPABILITY_EMISSION_WINDOW)
    assert row["maturity"] == MATURITY_INSTALLED
    # process_resources + loaded_bulk installed (0.61.8–9); intention stubs still off.
    assert CAPABILITY_PROCESS_RESOURCES in reg
    assert reg.is_enabled(CAPABILITY_PROCESS_RESOURCES)
    pr = next(r for r in reg.catalog() if r["id"] == CAPABILITY_PROCESS_RESOURCES)
    assert pr["maturity"] == MATURITY_INSTALLED
    assert CAPABILITY_LOADED_BULK in reg
    assert reg.is_enabled(CAPABILITY_LOADED_BULK)
    lb = next(r for r in reg.catalog() if r["id"] == CAPABILITY_LOADED_BULK)
    assert lb["maturity"] == MATURITY_INSTALLED
    assert "boot_membership" not in reg
    assert "system_log_tail" not in reg
    assert CAPABILITY_MONITOR_AGENT in reg
    assert not reg.is_enabled(CAPABILITY_MONITOR_AGENT)
    intention = next(
        r for r in reg.catalog() if r["id"] == CAPABILITY_MONITOR_AGENT
    )
    assert intention["maturity"] == MATURITY_INTENTION


def test_registry_enable_disable_clone() -> None:
    reg = default_vitality_registry()
    reg.disable(CAPABILITY_EMISSION_WINDOW)
    assert not reg.is_enabled(CAPABILITY_EMISSION_WINDOW)
    clone = reg.clone()
    clone.enable(CAPABILITY_EMISSION_WINDOW)
    assert not reg.is_enabled(CAPABILITY_EMISSION_WINDOW)
    assert clone.is_enabled(CAPABILITY_EMISSION_WINDOW)


def test_custom_capability_registration() -> None:
    calls: list[str] = []

    def _sample(inst: Any, ctx: SampleContext) -> CapabilityFragment:
        calls.append("x")
        return CapabilityFragment.ok("custom_eye", {"n": 1})

    reg = VitalityRegistry()
    reg.register(
        VitalityCapability(id="custom_eye", sample=_sample, order=1),
        enabled=True,
    )
    snap = VitalityProjection(reg).sample(object())
    assert "custom_eye" in snap.fragments
    assert snap.fragments["custom_eye"].data["n"] == 1
    assert calls == ["x"]


# ── projection fold ──────────────────────────────────────────────────────────


def test_project_started_runtime_seat_walk() -> None:
    rt = BaseRuntime()
    rt.start(storage_backend="memory")
    try:
        snap = project(rt)
        assert snap.schema == VITALITY_SNAPSHOT_SCHEMA
        assert CAPABILITY_SEAT_WALK in snap.fragments
        frag = snap.fragments[CAPABILITY_SEAT_WALK]
        assert frag.present is True
        assert frag.state == STATE_OK
        assert len(snap.seats) > 0
        assert snap.summary["present_count"] > 0
        assert SEAT_WAIT_PLANE in snap.summary["present_ids"]

        # Lineage ties seats to seat_walk capability.
        seat_lines = [row for row in snap.lineage if row.get("seat_id")]
        assert any(row["seat_id"] == SEAT_WAIT_PLANE for row in seat_lines)
        assert all(row["capability_id"] == CAPABILITY_SEAT_WALK for row in seat_lines)

        # Installed observe caps run by default; intention stubs stay off.
        assert CAPABILITY_EMISSION_WINDOW in snap.fragments
        assert CAPABILITY_PROCESS_RESOURCES in snap.fragments
        assert CAPABILITY_LOADED_BULK in snap.fragments
        assert CAPABILITY_MONITOR_AGENT not in snap.fragments
        assert "boot_membership" not in snap.fragments
        assert "system_log_tail" not in snap.fragments
    finally:
        rt.stop()


def test_project_top_view_structural() -> None:
    rt = BaseRuntime()
    rt.start(storage_backend="memory")
    try:
        top = project_top(rt)
        assert top["schema"] == VITALITY_SNAPSHOT_SCHEMA
        assert "summary" in top
        assert "seats" in top
        wait = next(s for s in top["seats"] if s["seat_id"] == SEAT_WAIT_PLANE)
        assert wait["present"] is True
        assert wait["lineage"] == LINEAGE_SAMPLED
        # Product present gets raw; system does not curate load.
        assert isinstance(wait.get("raw"), dict)
        assert wait.get("sample_source") == "doctor_snapshot"
    finally:
        rt.stop()


def test_projection_receives_reports_no_second_walk_in_bag() -> None:
    """seat_walk stores reports in bag; projection does not invent seats."""
    rt = BaseRuntime()
    rt.start(storage_backend="memory")
    try:
        direct = discover_seats(rt)
        snap = project_seat_walk_only(rt)
        assert len(snap.seats) == len(direct)
        assert {s.seat_id for s in snap.seats} == {s.seat_id for s in direct}
    finally:
        rt.stop()


def test_lean_shell_projection_honest_absent() -> None:
    from palm.system.vitality.schema import SEAT_PLANES

    class _Lean:
        is_started = False

    snap = project_seat_walk_only(_Lean())
    assert snap.summary["absent_count"] >= 3
    by_id = snap.seat_by_id()
    assert by_id[SEAT_PLANES].state == STATE_ABSENT
    # Members only expand when hub is present — not fake-absent from a menu.
    assert SEAT_WAIT_PLANE not in by_id


def test_disabled_seat_walk_empty_seats() -> None:
    reg = default_vitality_registry()
    reg.disable(CAPABILITY_SEAT_WALK)
    snap = VitalityProjection(reg).sample(object())
    assert CAPABILITY_SEAT_WALK not in snap.fragments
    assert snap.seats == []
    assert snap.summary["seat_count"] == 0


def test_only_unknown_capability_skipped() -> None:
    reg = default_vitality_registry()
    snap = VitalityProjection(reg).sample(
        object(),
        ProjectionOptions(only=frozenset({"no_such_cap"})),
    )
    assert snap.fragments["no_such_cap"].state == STATE_SKIPPED
    assert "no_such_cap" in snap.skipped_capabilities


def test_extra_enable_intention_returns_skipped_body() -> None:
    """Parked monitor_agent stub is registered; enabling it yields skipped, not fake ok."""
    reg = default_vitality_registry()
    snap = VitalityProjection(reg).sample(
        object(),
        ProjectionOptions(
            only=frozenset({CAPABILITY_MONITOR_AGENT}),
            extra_enable=frozenset({CAPABILITY_MONITOR_AGENT}),
        ),
    )
    frag = snap.fragments[CAPABILITY_MONITOR_AGENT]
    assert frag.state == STATE_SKIPPED
    assert "intention_not_implemented" in frag.notes[0]


def test_capability_error_becomes_error_fragment() -> None:
    def _boom(inst: Any, ctx: SampleContext) -> CapabilityFragment:
        raise RuntimeError("cap_fail")

    reg = VitalityRegistry()
    reg.register(
        VitalityCapability(id="boom", sample=_boom),
        enabled=True,
    )
    snap = VitalityProjection(reg).sample(object())
    assert snap.fragments["boom"].state == "error"
    assert "cap_fail" in snap.fragments["boom"].notes[0]


def test_snapshot_to_dict_schema() -> None:
    rt = BaseRuntime()
    rt.start(storage_backend="memory")
    try:
        d = project(rt).to_dict()
        assert d["schema"] == VITALITY_SNAPSHOT_SCHEMA
        assert CAPABILITY_SEAT_WALK in d["fragments"]
        assert isinstance(d["seats"], list)
        assert isinstance(d["lineage"], list)
    finally:
        rt.stop()


def test_projection_does_not_start_services() -> None:
    rt = BaseRuntime()
    rt.start(storage_backend="memory")
    try:
        assert rt.supervisor is not None
        assert rt.supervisor.status()["running_count"] == 0
        project(rt)
        assert rt.supervisor.status()["running_count"] == 0
    finally:
        rt.stop()
