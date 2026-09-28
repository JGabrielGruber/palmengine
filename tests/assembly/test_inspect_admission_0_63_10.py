"""0.63.10 — inspect top/vitality present living admission."""

from __future__ import annotations

from services.inspect.present import present_top, present_vitality

from palm.system.log import reset_system_log_for_tests
from palm.system.runtime.base import BaseRuntime
from palm.system.vitality.seats import reset_default_probe_catalog_for_tests
from tests.helpers.bound import bound_for_runtime


def test_present_top_includes_admission() -> None:
    reset_system_log_for_tests()
    reset_default_probe_catalog_for_tests()
    rt = BaseRuntime()
    rt.start(drivers=bound_for_runtime(storage_backend="memory"))
    try:
        top = present_top(rt)
        assert "admission" in top
        assert top["admission"]["may_run_business"] is True
        assert top["admission"]["definition_id"] == "local.embedded"
        vit = present_vitality(rt)
        assert vit["admission"]["may_run_business"] is True
    finally:
        rt.stop()


def test_present_top_admission_fail_closed_when_skipped() -> None:
    reset_system_log_for_tests()
    reset_default_probe_catalog_for_tests()
    rt = BaseRuntime()
    rt.start(drivers=bound_for_runtime(storage_backend="memory"), structure_skip=True)
    try:
        top = present_top(rt)
        assert top["admission"]["may_run_business"] is False
    finally:
        rt.stop()
