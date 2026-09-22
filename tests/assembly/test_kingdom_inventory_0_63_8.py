"""0.63.8 — admission inventory: gated map + packaging admission pointer."""

from __future__ import annotations

from bundles.standard.app.host.application_host import ApplicationHost
from bundles.standard.app.settings import PalmSettings
from palm.system.log import reset_system_log_for_tests
from palm.system.runtime.base import BaseRuntime
from palm.system.structure import (
    GATED_PATHS,
    READINESS_EDGES,
    admission_inventory,
    admission_inventory_snapshot,
)


def test_admission_inventory_has_walls() -> None:
    m = admission_inventory()
    assert m["gated_count"] >= 8
    assert m["readiness_edge_count"] >= 1
    ids = {g["id"] for g in GATED_PATHS}
    assert "work_plane.tick" in ids
    assert "executor.submit_flow" in ids
    assert "definition.refuse" in ids
    assert "vitality.structure" in ids
    pret = {p["id"] for p in READINESS_EDGES}
    assert "env.structure_toggles" in pret


def test_admission_inventory_snapshot_live() -> None:
    reset_system_log_for_tests()
    rt = BaseRuntime()
    rt.start(storage_backend="memory")
    try:
        snap = admission_inventory_snapshot(rt)
        assert snap["live"]["is_started"] is True
        assert snap["live"]["admission"]["may_run_business"] is True
        assert snap["live"]["definition_id"] == "local.embedded"
    finally:
        rt.stop()


def test_host_packaging_nests_assembly() -> None:
    reset_system_log_for_tests()
    settings = PalmSettings.for_tests(load_examples=False)
    host = ApplicationHost.for_mode("safe", settings=settings)
    host.start()
    try:
        bag = host.packaging_status()
        assert "structure" in bag
        assert bag["structure"]["role"] == "admission_pointer"
        assert bag["structure"]["may_run_business"] is True
        assert bag["structure"]["definition_id"] == "local.embedded"
        # Host surface
        assert host.admission.may_run_business is True
    finally:
        host.shutdown()


def test_host_admission_empty_before_start() -> None:
    host = ApplicationHost.for_mode("safe")
    assert host.admission.may_run_business is False
