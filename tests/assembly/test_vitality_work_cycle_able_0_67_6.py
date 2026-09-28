"""0.67.6 — vitality work_cycle drain is membership, not ready."""

from __future__ import annotations

from palm.core.structure import CAPABILITY_WORK_DRAIN
from palm.system.log import reset_system_log_for_tests
from palm.system.runtime.base import BaseRuntime
from palm.system.structure.inventory import GATED_PATHS, READINESS_EDGES, admission_inventory
from palm.system.vitality import RECIPE_WORK_CYCLE, STATE_OK, run_benchmark
from tests.helpers.bound import bound_for_runtime


def test_embedded_work_cycle_enqueues_without_drain() -> None:
    """Ready without work_drain still enqueues; tick does not process."""
    reset_system_log_for_tests()
    rt = BaseRuntime()
    rt.start(drivers=bound_for_runtime(storage_backend="memory"))
    try:
        assert rt.admission.may_run_business is True
        assert rt.admission.has_capability(CAPABILITY_WORK_DRAIN) is False
        frag = run_benchmark(rt, recipe=RECIPE_WORK_CYCLE, iterations=7)
        assert frag.state == STATE_OK
        meta = frag.data["recipe_meta"]
        assert meta["kind"] == RECIPE_WORK_CYCLE
        assert meta["enqueued"] == 7
        assert meta.get("processed", 0) == 0
        assert rt.work_plane.status()["pending"] == 7
    finally:
        rt.stop()


def test_cli_work_cycle_drains_when_organ_installed() -> None:
    reset_system_log_for_tests()
    rt = BaseRuntime()
    rt.start(
        drivers=bound_for_runtime(storage_backend="memory"), structure_definition_id="local.cli"
    )
    try:
        assert rt.admission.may_run_business is True
        assert rt.admission.has_capability(CAPABILITY_WORK_DRAIN) is True
        frag = run_benchmark(rt, recipe=RECIPE_WORK_CYCLE, iterations=7)
        assert frag.state == STATE_OK
        meta = frag.data["recipe_meta"]
        assert meta["enqueued"] == 7
        assert meta.get("processed", 0) >= 1
        assert rt.work_plane.status()["pending"] == 0
    finally:
        rt.stop()


def test_inventory_vitality_work_cycle_paid() -> None:
    gated = {row["id"] for row in GATED_PATHS}
    assert "vitality.work_cycle" in gated
    pretenders = {row["id"]: row["status"] for row in READINESS_EDGES}
    assert pretenders["vitality.work_cycle_edge"] == "paid_0_67_6"
    assert admission_inventory()["gated_count"] >= 1
