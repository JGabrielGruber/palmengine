"""0.61.8 — process_resources (stdlib RSS/CPU/threads)."""

from __future__ import annotations

import os

from palm.system.log import reset_system_log_for_tests
from palm.system.runtime.base import BaseRuntime
from palm.system.vitality import (
    CAPABILITY_PROCESS_RESOURCES,
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
    sample_process_resources,
)
from tests.helpers.bound import bound_for_runtime


def setup_function() -> None:
    reset_default_vitality_registry_for_tests()
    reset_system_log_for_tests()


def test_default_registry_process_resources_installed() -> None:
    reg = default_vitality_registry()
    assert CAPABILITY_PROCESS_RESOURCES in reg
    assert reg.is_enabled(CAPABILITY_PROCESS_RESOURCES)
    row = next(r for r in reg.catalog() if r["id"] == CAPABILITY_PROCESS_RESOURCES)
    assert row["maturity"] == MATURITY_INSTALLED
    assert row["cost"] == "cheap"


def test_sample_process_resources_stdlib() -> None:
    frag = sample_process_resources(object(), SampleContext())
    assert frag.capability_id == CAPABILITY_PROCESS_RESOURCES
    assert frag.present is True
    assert frag.state == STATE_OK
    assert frag.data["pid"] == os.getpid()
    summary = frag.data["summary"]
    assert summary["threads_active"] >= 1
    assert "resource" in summary["sources"] or "proc_status" in summary["sources"]
    # Memory: labeled primary RSS (current on Linux, peak when that is all we have).
    assert summary.get("primary_rss_kb") is not None
    assert summary["primary_rss_kind"] in {"current", "peak"}
    assert "user_s" in frag.data["cpu"]
    assert isinstance(frag.data["cpu"]["user_s"], float)
    # Units honesty for rusage peak when present.
    mem = frag.data["memory"]
    if "max_rss" in mem:
        assert mem["max_rss_unit"] in {"kilobytes", "bytes"}
    # Full raw stays on fragment for product present / diffs.
    assert "rusage" in frag.data["raw"] or "proc_status" in frag.data["raw"]


def test_bag_skip() -> None:
    ctx = SampleContext()
    ctx.bag["process_resources_skip"] = True
    frag = sample_process_resources(object(), ctx)
    assert frag.state == STATE_SKIPPED
    assert "process_resources_skip" in frag.notes[0]


def test_project_includes_process_resources_by_default() -> None:
    rt = BaseRuntime()
    rt.start(drivers=bound_for_runtime(storage_backend="memory"))
    try:
        snap = project(rt)
        assert CAPABILITY_SEAT_WALK in snap.fragments
        assert CAPABILITY_PROCESS_RESOURCES in snap.fragments
        pr = snap.fragments[CAPABILITY_PROCESS_RESOURCES]
        assert pr.state == STATE_OK
        assert pr.data["summary"]["primary_rss_kb"] is not None

        top = project_top(rt)
        assert "process" in top
        assert top["process"]["state"] == STATE_OK
        assert top["process"]["summary"]["pid"] == os.getpid()
        # Top stays light — no raw rusage dump.
        assert "raw" not in top["process"]
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
