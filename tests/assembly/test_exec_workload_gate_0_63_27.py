"""0.63.27 — product workload exec is a business path that needs admission (fail closed)."""

from __future__ import annotations

import pytest

from palm.system.log import reset_system_log_for_tests
from palm.system.runtime.base import BaseRuntime
from palm.system.structure.errors import AdmissionRefusedError
from palm.system.structure.inventory import GATED_PATHS, READINESS_EDGES
from tests.helpers.bound import bound_for_runtime


def test_exec_workload_refused_when_assembly_skipped() -> None:
    reset_system_log_for_tests()
    rt = BaseRuntime()
    rt.start(
        drivers=bound_for_runtime(storage_backend="memory"),
        structure_skip=True,
        workload_host_enabled=True,
    )
    try:
        assert rt.admission.may_run_business is False
        with pytest.raises(AdmissionRefusedError):
            rt.exec_workload("wl-missing", ["true"])
    finally:
        rt.stop()


def test_exec_workload_refused_when_dna_refuse_blocks() -> None:
    reset_system_log_for_tests()
    rt = BaseRuntime()
    rt.start(
        drivers=bound_for_runtime(storage_backend="memory"),
        structure_definition_id="local.embedded",
        structure_surfaces=["rest"],
        workload_host_enabled=True,
    )
    try:
        assert rt.admission.may_run_business is False
        with pytest.raises(AdmissionRefusedError):
            rt.exec_workload("wl-missing", ["true"])
    finally:
        rt.stop()


def test_exec_workload_allowed_when_admitted_reaches_engine() -> None:
    reset_system_log_for_tests()
    rt = BaseRuntime()
    rt.start(drivers=bound_for_runtime(storage_backend="memory"), workload_host_enabled=True)
    try:
        assert rt.admission.may_run_business is True
        try:
            rt.exec_workload("wl-does-not-exist", ["true"])
        except Exception as exc:
            assert not isinstance(exc, AdmissionRefusedError)
            assert "Admission" not in type(exc).__name__
    finally:
        rt.stop()


def test_stop_workload_not_admission_citizen() -> None:
    """Stop stays available when admission is closed (shutdown / cleanup)."""
    reset_system_log_for_tests()
    rt = BaseRuntime()
    rt.start(
        drivers=bound_for_runtime(storage_backend="memory"),
        structure_skip=True,
        workload_host_enabled=True,
    )
    try:
        assert rt.admission.may_run_business is False
        try:
            rt.stop_workload("wl-missing")
        except Exception as exc:
            assert not isinstance(exc, AdmissionRefusedError)
    finally:
        rt.stop()


def test_engine_exec_not_gated_by_port() -> None:
    reset_system_log_for_tests()
    rt = BaseRuntime()
    rt.start(
        drivers=bound_for_runtime(storage_backend="memory"),
        structure_skip=True,
        workload_host_enabled=True,
    )
    try:
        engine = rt.workload
        assert engine is not None
        try:
            engine.exec("wl-missing", ["true"])
        except Exception as exc:
            assert not isinstance(exc, AdmissionRefusedError)
    finally:
        rt.stop()


def test_inventory_exec_workload_and_named_stop() -> None:
    gated = {row["id"] for row in GATED_PATHS}
    assert "execution.exec_workload" in gated
    pretenders = {row["id"]: row["status"] for row in READINESS_EDGES}
    assert pretenders["execution.stop_workload_ungated"] == "named_0_63_27"
    assert pretenders["execution.workload_engine_dig"] == "named_0_63_27"
