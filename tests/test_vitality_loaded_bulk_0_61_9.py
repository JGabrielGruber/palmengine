"""0.61.9 — loaded_bulk (attached seats · modules · composition)."""

from __future__ import annotations

from palm.system.log import reset_system_log_for_tests
from palm.system.runtime.base import BaseRuntime
from palm.system.vitality import (
    CAPABILITY_LOADED_BULK,
    CAPABILITY_SEAT_WALK,
    MATURITY_INSTALLED,
    STATE_OK,
    STATE_SKIPPED,
    ProjectionOptions,
    SampleContext,
    default_vitality_registry,
    project,
    project_top,
    reset_default_vitality_registry_for_tests,
    sample_loaded_bulk,
)
from tests.helpers.bound import bound_for_runtime


def setup_function() -> None:
    reset_default_vitality_registry_for_tests()
    reset_system_log_for_tests()


def test_default_registry_loaded_bulk_installed() -> None:
    reg = default_vitality_registry()
    assert CAPABILITY_LOADED_BULK in reg
    assert reg.is_enabled(CAPABILITY_LOADED_BULK)
    row = next(r for r in reg.catalog() if r["id"] == CAPABILITY_LOADED_BULK)
    assert row["maturity"] == MATURITY_INSTALLED
    assert row["cost"] == "cheap"


def test_sample_loaded_bulk_after_boot() -> None:
    rt = BaseRuntime()
    rt.start(drivers=bound_for_runtime(storage_backend="memory"))
    try:
        frag = sample_loaded_bulk(rt, SampleContext())
        assert frag.capability_id == CAPABILITY_LOADED_BULK
        assert frag.present is True
        assert frag.state == STATE_OK
        assert "visibility_not_shame" in frag.notes
        summary = frag.data["summary"]
        assert summary["attached_object_count"] > 0
        assert summary["unique_module_count"] > 0
        # At least one seat maps to a palm module with a .py file.
        assert summary.get("modules_with_lines", 0) > 0
        assert summary.get("total_module_lines") is not None
        assert summary["total_module_lines"] > 0
        # Composition membership is visible.
        comp = frag.data["composition"]
        assert comp["present_seat_count"] > 0
        assert comp["planes_registered"] is not None
        assert comp["planes_registered"] >= 1
        # Seats carry type/module bulk — not health grades.
        wait = next(
            (s for s in frag.data["seats"] if s["seat_id"] == "wait_plane"),
            None,
        )
        assert wait is not None
        assert wait["module"]
        assert isinstance(wait["public_callables"], int)
        assert wait["public_callables"] >= 0
        # Ranked modules are light rows, largest lines first when known.
        modules = frag.data["modules"]
        assert modules
        if modules[0].get("lines") is not None:
            assert all(
                (modules[i].get("lines") or 0) >= (modules[i + 1].get("lines") or 0)
                or modules[i + 1].get("lines") is None
                for i in range(min(2, len(modules) - 1))
            )
    finally:
        rt.stop()


def test_bag_skip() -> None:
    ctx = SampleContext()
    ctx.bag["loaded_bulk_skip"] = True
    frag = sample_loaded_bulk(object(), ctx)
    assert frag.state == STATE_SKIPPED
    assert "loaded_bulk_skip" in frag.notes[0]


def test_project_includes_loaded_bulk_by_default() -> None:
    rt = BaseRuntime()
    rt.start(drivers=bound_for_runtime(storage_backend="memory"))
    try:
        snap = project(rt)
        assert CAPABILITY_SEAT_WALK in snap.fragments
        assert CAPABILITY_LOADED_BULK in snap.fragments
        lb = snap.fragments[CAPABILITY_LOADED_BULK]
        assert lb.state == STATE_OK
        assert lb.data["summary"]["attached_object_count"] > 0

        top = project_top(rt)
        assert "bulk" in top
        assert top["bulk"]["state"] == STATE_OK
        assert "top_modules" in top["bulk"]["summary"]
        # Top stays light — no full seats table.
        assert "seats" not in top["bulk"]
    finally:
        rt.stop()


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
