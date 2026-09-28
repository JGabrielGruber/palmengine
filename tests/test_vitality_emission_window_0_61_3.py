"""0.61.3 — emission_window + actor_kind partition."""

from __future__ import annotations

from palm.system.log import get_system_log, reset_system_log_for_tests
from palm.system.runtime.base import BaseRuntime
from palm.system.vitality import (
    ACTOR_KIND_AGENT,
    ACTOR_KIND_SYSTEM,
    ACTOR_KIND_UNKNOWN,
    CAPABILITY_EMISSION_WINDOW,
    CAPABILITY_SEAT_WALK,
    CHANNEL_SYSTEM_LOG,
    MATURITY_INSTALLED,
    STATE_OK,
    ProjectionOptions,
    SampleContext,
    coerce_actor_kind,
    default_vitality_registry,
    project,
    project_top,
    reset_default_vitality_registry_for_tests,
    sample_emission_window,
)
from tests.helpers.bound import bound_for_runtime


def setup_function() -> None:
    reset_default_vitality_registry_for_tests()
    reset_system_log_for_tests()


def test_coerce_actor_kind_known_and_unknown() -> None:
    assert coerce_actor_kind("human") == "human"
    assert coerce_actor_kind("AGENT") == ACTOR_KIND_AGENT
    assert coerce_actor_kind("bot") == ACTOR_KIND_UNKNOWN
    assert coerce_actor_kind(None) == ACTOR_KIND_UNKNOWN
    assert coerce_actor_kind("") == ACTOR_KIND_UNKNOWN


def test_default_registry_emission_window_installed() -> None:
    reg = default_vitality_registry()
    assert CAPABILITY_EMISSION_WINDOW in reg
    assert reg.is_enabled(CAPABILITY_EMISSION_WINDOW)
    row = next(r for r in reg.catalog() if r["id"] == CAPABILITY_EMISSION_WINDOW)
    assert row["maturity"] == MATURITY_INSTALLED


def test_sample_emission_window_after_boot() -> None:
    rt = BaseRuntime()
    rt.start(drivers=bound_for_runtime(storage_backend="memory"))
    try:
        frag = sample_emission_window(rt, SampleContext())
        assert frag.capability_id == CAPABILITY_EMISSION_WINDOW
        assert frag.present is True
        assert frag.state == STATE_OK
        summary = frag.data["summary"]
        assert summary["emission_count"] > 0
        assert CHANNEL_SYSTEM_LOG in summary["sources"]
        # Boot tape is system narrative — partition shows system, not silent blend.
        assert summary["by_actor_kind"].get(ACTOR_KIND_SYSTEM, 0) > 0
        assert summary["unknown_actor_count"] == 0
        row = frag.data["emissions"][0]
        assert row["channel"] == CHANNEL_SYSTEM_LOG
        assert row["actor_kind"] == ACTOR_KIND_SYSTEM
        assert "outcome" in row and "kind" in row and "time" in row
        # Optional heat when work plane is attached.
        assert "heat" in frag.data
        assert frag.data["heat"]["attached"] is True
    finally:
        rt.stop()


def test_declared_actor_kind_partitions() -> None:
    slog = get_system_log()
    slog.info(
        "assist.turn",
        "declared agent emission",
        actor_kind="agent",
        session_id="sess-test-1",
    )
    slog.info(
        "mystery.blip",
        "no actor field",
    )
    frag = sample_emission_window(object(), SampleContext())
    by = frag.data["summary"]["by_actor_kind"]
    assert by.get(ACTOR_KIND_AGENT, 0) >= 1
    # mystery.blip has no actor_kind → channel default system (not invented human).
    assert by.get(ACTOR_KIND_SYSTEM, 0) >= 1
    agents = [e for e in frag.data["emissions"] if e.get("actor_kind") == ACTOR_KIND_AGENT]
    assert agents
    assert agents[-1]["actor_source"] == "declared"
    assert agents[-1]["session_subject"] == "sess-test-1"


def test_invalid_declared_actor_is_unknown() -> None:
    slog = get_system_log()
    slog.info("x", "bad actor", actor_kind="not-a-kind")
    frag = sample_emission_window(object(), SampleContext())
    bad = [
        e
        for e in frag.data["emissions"]
        if e.get("event") == "x" and e.get("message") == "bad actor"
    ]
    assert bad
    assert bad[-1]["actor_kind"] == ACTOR_KIND_UNKNOWN
    assert bad[-1]["actor_source"] == "declared"
    assert frag.data["summary"]["unknown_actor_count"] >= 1


def test_project_includes_emission_window_by_default() -> None:
    rt = BaseRuntime()
    rt.start(drivers=bound_for_runtime(storage_backend="memory"))
    try:
        snap = project(rt)
        assert CAPABILITY_SEAT_WALK in snap.fragments
        assert CAPABILITY_EMISSION_WINDOW in snap.fragments
        em = snap.fragments[CAPABILITY_EMISSION_WINDOW]
        assert em.state == STATE_OK
        assert em.data["summary"]["emission_count"] > 0

        top = project_top(rt)
        assert "emissions" in top
        assert top["emissions"]["sample_count"] > 0
        assert ACTOR_KIND_SYSTEM in top["emissions"]["summary"]["by_actor_kind"]
    finally:
        rt.stop()


def test_window_limit_bag() -> None:
    slog = get_system_log()
    for i in range(15):
        slog.info(f"fill.{i}", f"n={i}")
    ctx = SampleContext()
    ctx.bag["emission_window_limit"] = 5
    frag = sample_emission_window(object(), ctx)
    assert frag.data["summary"]["window_limit"] == 5
    assert frag.data["summary"]["emission_count"] == 5


def test_projection_still_does_not_start_services() -> None:
    rt = BaseRuntime()
    rt.start(drivers=bound_for_runtime(storage_backend="memory"))
    try:
        assert rt.supervisor is not None
        assert rt.supervisor.status()["running_count"] == 0
        project(rt, ProjectionOptions())
        assert rt.supervisor.status()["running_count"] == 0
    finally:
        rt.stop()
