"""0.63.33 — host packaging business start / continue doors need admission; kernel dig named."""

from __future__ import annotations

import pytest

from bundles.standard.app.host.application_host import ApplicationHost
from bundles.standard.app.settings import PalmSettings
from palm.common.cqrs.command import CancelJobCommand, SubmitFlowCommand
from palm.system.log import reset_system_log_for_tests
from palm.system.structure.errors import AdmissionRefusedError
from palm.system.structure.inventory import GATED_PATHS, READINESS_EDGES, admission_inventory


def _settings() -> PalmSettings:
    return PalmSettings(
        load_example_definitions=True,
        storage_backend="memory",
        rebuild_projections_on_startup=False,
        reconcile_instances_on_startup=False,
    )


def test_host_submit_flow_refused_when_assembly_skipped() -> None:
    reset_system_log_for_tests()
    host = ApplicationHost.for_mode("all_in_one", settings=_settings())
    host.start(structure_skip=True)
    try:
        assert host.admission.may_run_business is False
        with pytest.raises(AdmissionRefusedError):
            host.submit_flow("todo-builder")
        with pytest.raises(AdmissionRefusedError):
            host.submit_process("does-not-matter")
        with pytest.raises(AdmissionRefusedError):
            host.provide_input("job-x", "v")
        with pytest.raises(AdmissionRefusedError):
            host.resume_process("inst-x")
        with pytest.raises(AdmissionRefusedError):
            host.invoke_resource("res-x", action="ping")
    finally:
        host.shutdown()


def test_host_execute_submit_flow_refused_when_assembly_skipped() -> None:
    """CQRS bus path also fails closed (not only thin host wrappers)."""
    reset_system_log_for_tests()
    host = ApplicationHost.for_mode("all_in_one", settings=_settings())
    host.start(structure_skip=True)
    try:
        with pytest.raises(AdmissionRefusedError):
            host.execute(SubmitFlowCommand(flow="todo-builder"))
    finally:
        host.shutdown()


def test_host_cancel_job_not_admission_citizen() -> None:
    """Cancel remains control residual on packaging CQRS (named_0_63_30)."""
    reset_system_log_for_tests()
    host = ApplicationHost.for_mode("all_in_one", settings=_settings())
    host.start(structure_skip=True)
    try:
        assert host.admission.may_run_business is False
        result = host.execute(CancelJobCommand(job_id="job-missing"))
        assert isinstance(result, dict)
        assert result.get("found") is False or "job_id" in result
    finally:
        host.shutdown()


def test_inventory_host_packaging_and_kernel_residual() -> None:
    gated = {row["id"] for row in GATED_PATHS}
    assert "host.packaging_start_continue" in gated
    pretenders = {row["id"]: row["status"] for row in READINESS_EDGES}
    assert pretenders["host.packaging_start_continue_edge"] == "paid_0_63_33"
    assert pretenders["kernel.direct_dig"] == "named_0_63_33"
    assert admission_inventory()["gated_count"] >= 1
