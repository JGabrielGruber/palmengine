"""0.63.31 — execution product façades use published admission at the edge."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from bundles.standard.app.host.application_host import ApplicationHost
from bundles.standard.app.settings import PalmSettings
from palm.common.cqrs.bus import CommandBus, QueryBus
from palm.core.structure import AdmissionSnapshot, StructurePhase
from palm.services.execution.processes.service import ProcessExecutionService
from palm.services.execution.providers.service import ProviderExecutionService
from palm.services.execution.workloads.service import WorkloadExecutionService
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


def _closed() -> AdmissionSnapshot:
    return AdmissionSnapshot(
        may_run_business=False,
        phase=StructurePhase.BLOCKED,
        reasons=("test_closed",),
    )


def _bus_kw() -> dict:
    return {
        "commands": CommandBus(),
        "queries": QueryBus(),
        "schemas": MagicMock(),
    }


def test_workload_start_refused_on_oath_without_runtime_dig() -> None:
    svc = WorkloadExecutionService(
        **_bus_kw(),
        admission_source=lambda: _closed(),
    )
    svc.resolve_runtime = MagicMock(  # type: ignore[method-assign]
        side_effect=AssertionError("published admission broken: resolve_runtime used for admission")
    )
    with pytest.raises(AdmissionRefusedError, match="test_closed"):
        # Gate runs before spec parse — body shape irrelevant when refused.
        svc.start({"kind": "run", "image": "x"})
    svc.resolve_runtime.assert_not_called()


def test_workload_exec_refused_on_oath() -> None:
    svc = WorkloadExecutionService(
        **_bus_kw(),
        admission_source=lambda: _closed(),
    )
    with pytest.raises(AdmissionRefusedError, match="test_closed"):
        svc.exec("wl-1", ["echo", "hi"])


def test_workload_stop_not_admission_citizen() -> None:
    port = MagicMock()
    port.stop_workload.return_value = MagicMock(to_dict=lambda: {"id": "wl-1", "status": "stopped"})
    runtime = MagicMock()
    runtime.execution = port
    svc = WorkloadExecutionService(
        **_bus_kw(),
        runtime=runtime,
        admission_source=lambda: _closed(),
    )
    body = svc.stop("wl-1")
    assert body["id"] == "wl-1"
    port.stop_workload.assert_called_once_with("wl-1")


def test_provider_invoke_refused_on_oath_without_runtime_dig() -> None:
    svc = ProviderExecutionService(
        **_bus_kw(),
        admission_source=lambda: _closed(),
    )
    svc.resolve_runtime = MagicMock(  # type: ignore[method-assign]
        side_effect=AssertionError("published admission broken: resolve_runtime used for admission")
    )
    with pytest.raises(AdmissionRefusedError, match="test_closed"):
        svc.invoke("res-1", action="get")
    svc.resolve_runtime.assert_not_called()


def test_process_run_refused_on_oath() -> None:
    svc = ProcessExecutionService(
        **_bus_kw(),
        admission_source=lambda: _closed(),
    )
    svc.resolve_runtime = MagicMock(  # type: ignore[method-assign]
        side_effect=AssertionError("published admission broken")
    )
    with pytest.raises(AdmissionRefusedError, match="test_closed"):
        svc.run("proc-1")
    svc.resolve_runtime.assert_not_called()


def test_process_submit_refused_on_oath() -> None:
    svc = ProcessExecutionService(
        **_bus_kw(),
        admission_source=lambda: _closed(),
    )
    with pytest.raises(AdmissionRefusedError, match="test_closed"):
        svc.submit(["plan-1"])


def test_process_prepare_refused_on_oath() -> None:
    svc = ProcessExecutionService(
        **_bus_kw(),
        admission_source=lambda: _closed(),
    )
    with pytest.raises(AdmissionRefusedError, match="test_closed"):
        svc.prepare("proc-1")


def test_host_execution_facade_refused_when_assembly_skipped() -> None:
    reset_system_log_for_tests()
    host = ApplicationHost.for_mode("all_in_one", settings=_settings())
    host.start(structure_skip=True)
    try:
        assert host.admission.may_run_business is False
        with pytest.raises(AdmissionRefusedError):
            host.execution.workloads.start({"kind": "run", "image": "x"})
        with pytest.raises(AdmissionRefusedError):
            host.execution.providers.invoke("missing-resource", action="get")
        with pytest.raises(AdmissionRefusedError):
            host.execution.processes.run("missing-process")
    finally:
        host.shutdown()


def test_inventory_execution_facade_oath() -> None:
    gated = {row["id"] for row in GATED_PATHS}
    assert "execution.product_facade_admission" in gated
    pretenders = {row["id"]: row["status"] for row in READINESS_EDGES}
    assert pretenders["execution.product_facade_edge"] == "paid_0_63_31"
    assert pretenders["workloads.product_stop_ungated"] == "named_0_63_31"
    assert admission_inventory()["gated_count"] >= 1
