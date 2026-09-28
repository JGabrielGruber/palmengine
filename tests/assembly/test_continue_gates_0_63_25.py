"""0.63.25 — product continue doors are business paths that need admission; not-this-door residuals named."""

from __future__ import annotations

import pytest

from palm.system.log import reset_system_log_for_tests
from palm.system.runtime.base import BaseRuntime
from palm.system.structure.errors import AdmissionRefusedError
from palm.system.structure.inventory import GATED_PATHS, READINESS_EDGES, admission_inventory
from tests.helpers.bound import bound_for_runtime


def test_resume_job_refused_when_assembly_skipped() -> None:
    reset_system_log_for_tests()
    rt = BaseRuntime()
    rt.start(drivers=bound_for_runtime(storage_backend="memory"), structure_skip=True)
    try:
        assert rt.admission.may_run_business is False
        with pytest.raises(AdmissionRefusedError):
            rt.resume_job("job-missing")
    finally:
        rt.stop()


def test_provide_input_refused_when_assembly_skipped() -> None:
    reset_system_log_for_tests()
    rt = BaseRuntime()
    rt.start(drivers=bound_for_runtime(storage_backend="memory"), structure_skip=True)
    try:
        assert rt.admission.may_run_business is False
        with pytest.raises(AdmissionRefusedError):
            rt.provide_input("job-missing", "x")
    finally:
        rt.stop()


def test_resume_job_allowed_when_admitted_reaches_orchestrator() -> None:
    """Admission open → gate does not refuse; missing job is orchestration error."""
    reset_system_log_for_tests()
    rt = BaseRuntime()
    rt.start(drivers=bound_for_runtime(storage_backend="memory"))
    try:
        assert rt.admission.may_run_business is True
        try:
            rt.resume_job("job-does-not-exist")
        except Exception as exc:
            assert not isinstance(exc, AdmissionRefusedError)
            assert "Admission" not in type(exc).__name__
    finally:
        rt.stop()


def test_orch_resume_not_gated_as_product_door() -> None:
    """Wait-plane spine dig — named residual, not ExecutionPort admission path."""
    reset_system_log_for_tests()
    rt = BaseRuntime()
    rt.start(drivers=bound_for_runtime(storage_backend="memory"), structure_skip=True)
    try:
        assert rt.admission.may_run_business is False
        try:
            rt.orchestration.resume_job("job-missing")
        except Exception as exc:
            assert not isinstance(exc, AdmissionRefusedError)
    finally:
        rt.stop()


def test_inventory_continue_citizens_and_named_digs() -> None:
    gated = {row["id"] for row in GATED_PATHS}
    assert "execution.resume_job" in gated
    assert "runtime.provide_input" in gated
    pretenders = {row["id"]: row["status"] for row in READINESS_EDGES}
    assert pretenders["execution.workload_engine_dig"] in (
        "named_0_63_25",
        "named_0_63_27",
    )
    assert pretenders["execution.resource_engine_dig"] == "named_0_63_25"
    # 0.63.26 paid wait-plane able; row remains for cartography history.
    assert pretenders["wait_plane.orch_resume_dig"] in (
        "named_0_63_25",
        "paid_0_63_26",
    )
    assert admission_inventory()["readiness_edge_count"] >= 3
