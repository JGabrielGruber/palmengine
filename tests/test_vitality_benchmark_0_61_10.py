"""0.61.10 — benchmark tool (recipe · observe snapshot diff)."""

from __future__ import annotations

from palm.system.log import reset_system_log_for_tests
from palm.system.runtime.base import BaseRuntime
from palm.system.vitality import (
    CAPABILITY_BENCHMARK,
    CAPABILITY_SEAT_WALK,
    DEFAULT_RECIPE,
    MATURITY_INSTALLED,
    RECIPE_IDLE,
    RECIPE_LOG_FILL,
    RECIPE_PULSE,
    RECIPE_WORK_CYCLE,
    ROLE_TOOL,
    STATE_OK,
    STATE_SKIPPED,
    ProjectionOptions,
    SampleContext,
    default_vitality_registry,
    diff_load_points,
    extract_load_points,
    project,
    project_top,
    reset_default_vitality_registry_for_tests,
    run_benchmark,
    sample_benchmark,
)
from tests.helpers.bound import bound_for_runtime


def setup_function() -> None:
    reset_default_vitality_registry_for_tests()
    reset_system_log_for_tests()


def test_default_registry_benchmark_installed_off() -> None:
    reg = default_vitality_registry()
    assert CAPABILITY_BENCHMARK in reg
    assert not reg.is_enabled(CAPABILITY_BENCHMARK)
    row = next(r for r in reg.catalog() if r["id"] == CAPABILITY_BENCHMARK)
    assert row["maturity"] == MATURITY_INSTALLED
    assert row["role"] == ROLE_TOOL
    assert row["default_enabled"] is False
    assert row["cost"] == "moderate"


def test_project_does_not_run_benchmark_by_default() -> None:
    rt = BaseRuntime()
    rt.start(drivers=bound_for_runtime(storage_backend="memory"))
    try:
        snap = project(rt)
        assert CAPABILITY_SEAT_WALK in snap.fragments
        assert CAPABILITY_BENCHMARK not in snap.fragments
        top = project_top(rt)
        assert "benchmark" not in top
    finally:
        rt.stop()


def test_run_benchmark_pulse_diff_shape() -> None:
    rt = BaseRuntime()
    rt.start(drivers=bound_for_runtime(storage_backend="memory"))
    try:
        frag = run_benchmark(rt, recipe=RECIPE_PULSE, iterations=5)
        assert frag.capability_id == CAPABILITY_BENCHMARK
        assert frag.present is True
        assert frag.state == STATE_OK
        assert "consumes_projection" in frag.notes
        assert frag.data["recipe"] == RECIPE_PULSE
        assert frag.data["iterations"] == 5
        assert frag.data["recipe_meta"]["ops"] == 5
        assert "work_plane.status" in frag.data["recipe_meta"]["path"]
        # Load points come from observe projection (process · seats · …).
        assert "rss_kb" in frag.data["before"] or "seat_present" in frag.data["before"]
        assert "diff" in frag.data
        assert "deltas" in frag.data["summary"]
        assert frag.data["summary"]["recipe_ms"] >= 0
        assert frag.data["timing"]["total_ms"] >= frag.data["timing"]["recipe_ms"]
    finally:
        rt.stop()


def test_log_fill_raises_emission_count() -> None:
    rt = BaseRuntime()
    rt.start(drivers=bound_for_runtime(storage_backend="memory"))
    try:
        frag = run_benchmark(rt, recipe=RECIPE_LOG_FILL, iterations=12)
        assert frag.state == STATE_OK
        before_em = frag.data["before"].get("emission_count")
        after_em = frag.data["after"].get("emission_count")
        assert before_em is not None and after_em is not None
        # Window is capped; still expect non-decreasing and probe partition.
        assert after_em >= before_em
        delta = frag.data["diff"]["emission_count"]["delta"]
        assert delta is not None
        assert delta >= 0
        # Declared actor_kind=probe should appear in after points when present.
        probe_after = frag.data["after"].get("emission_probe")
        if probe_after is not None:
            assert probe_after >= 1
    finally:
        rt.stop()


def test_idle_recipe_control() -> None:
    rt = BaseRuntime()
    rt.start(drivers=bound_for_runtime(storage_backend="memory"))
    try:
        frag = run_benchmark(rt, recipe=RECIPE_IDLE, iterations=3)
        assert frag.data["recipe_meta"]["ops"] == 0
        assert frag.data["recipe"] == RECIPE_IDLE
    finally:
        rt.stop()


def test_diff_load_points_pure() -> None:
    before = {"rss_kb": 100, "emission_count": 10, "sample_ts": "a"}
    after = {"rss_kb": 120, "emission_count": 10, "sample_ts": "b"}
    d = diff_load_points(before, after)
    assert d["rss_kb"]["delta"] == 20
    assert d["emission_count"]["delta"] == 0
    assert "delta" not in d["sample_ts"]


def test_extract_load_points_from_project() -> None:
    rt = BaseRuntime()
    rt.start(drivers=bound_for_runtime(storage_backend="memory"))
    try:
        snap = project(rt)
        points = extract_load_points(snap)
        assert points.get("seat_present", 0) > 0
        assert points.get("rss_kb") is not None
    finally:
        rt.stop()


def test_extra_enable_runs_tool_once() -> None:
    rt = BaseRuntime()
    rt.start(drivers=bound_for_runtime(storage_backend="memory"))
    try:
        snap = project(
            rt,
            ProjectionOptions(
                only=frozenset({CAPABILITY_BENCHMARK}),
                extra_enable=frozenset({CAPABILITY_BENCHMARK}),
            ),
        )
        frag = snap.fragments[CAPABILITY_BENCHMARK]
        assert frag.state == STATE_OK
        assert frag.data["recipe"] == DEFAULT_RECIPE == RECIPE_WORK_CYCLE
        top = snap.top_view()
        assert "benchmark" in top
        assert top["benchmark"]["summary"]["recipe"] == RECIPE_WORK_CYCLE
    finally:
        rt.stop()


def test_work_cycle_enqueues_and_drains() -> None:
    """Drain needs work_drain. Default DNA is ready without it (0.67.6)."""
    rt = BaseRuntime()
    rt.start(
        drivers=bound_for_runtime(storage_backend="memory"), structure_definition_id="local.cli"
    )
    try:
        frag = run_benchmark(rt, recipe=RECIPE_WORK_CYCLE, iterations=7)
        assert frag.state == STATE_OK
        meta = frag.data["recipe_meta"]
        assert meta["kind"] == RECIPE_WORK_CYCLE
        assert meta["enqueued"] == 7
        assert meta["path"] == "work_plane.enqueue+tick"
        assert meta.get("peak_pending", 0) >= 1
        # Missing flow → submit_ok 0; intents still leave the pending queue.
        assert meta.get("submit_ok", 0) == 0
        assert meta.get("processed", 0) >= 1
        assert meta.get("pending_after") in (0, None) or meta.get("pending_after") == 0
        assert rt.work_plane.status()["pending"] == 0
        assert meta.get("workers", 1) == 1
    finally:
        rt.stop()


def test_work_cycle_multi_claimer_drains() -> None:
    """0.62.6 — concurrent claimers clear queue without double-own.

    Pin ``local.cli`` so tick is drain-able (0.67.6). Embedded ready is not membership.
    """
    rt = BaseRuntime()
    rt.start(
        drivers=bound_for_runtime(storage_backend="memory"), structure_definition_id="local.cli"
    )
    try:
        frag = run_benchmark(rt, recipe=RECIPE_WORK_CYCLE, iterations=15, workers=3)
        assert frag.state == STATE_OK
        meta = frag.data["recipe_meta"]
        assert meta["enqueued"] == 15
        assert meta.get("workers") == 3
        assert meta.get("pending_after") in (0, None) or meta.get("pending_after") == 0
        assert rt.work_plane.status()["pending"] == 0
        assert "wall_ms" in meta
    finally:
        rt.stop()


def test_bag_skip_and_unknown_recipe_fallback() -> None:
    ctx = SampleContext()
    ctx.bag["benchmark_skip"] = True
    frag = sample_benchmark(object(), ctx)
    assert frag.state == STATE_SKIPPED

    rt = BaseRuntime()
    rt.start(drivers=bound_for_runtime(storage_backend="memory"))
    try:
        ctx2 = SampleContext()
        ctx2.bag["benchmark_recipe"] = "not_a_recipe"
        ctx2.bag["benchmark_iterations"] = 2
        frag2 = sample_benchmark(rt, ctx2)
        assert frag2.state == STATE_OK
        assert frag2.data["recipe"] == DEFAULT_RECIPE == RECIPE_WORK_CYCLE
        assert any("unknown_recipe_fallback" in n for n in frag2.notes)
    finally:
        rt.stop()


def test_benchmark_does_not_start_services() -> None:
    rt = BaseRuntime()
    rt.start(drivers=bound_for_runtime(storage_backend="memory"))
    try:
        assert rt.supervisor is not None
        assert rt.supervisor.status()["running_count"] == 0
        run_benchmark(rt, recipe=RECIPE_PULSE, iterations=8)
        assert rt.supervisor.status()["running_count"] == 0
    finally:
        rt.stop()
