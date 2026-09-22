"""0.63.32 — flow product start doors are business paths that need admission; list/describe soft residual."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from bundles.standard.app.host.application_host import ApplicationHost
from bundles.standard.app.settings import PalmSettings
from palm.common.cqrs.bus import CommandBus, QueryBus
from palm.core.structure import AdmissionSnapshot, StructurePhase
from palm.services.execution.flows.service import FlowExecutionService
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


def _flows_with_closed_inject() -> FlowExecutionService:
    closed = AdmissionSnapshot(
        may_run_business=False,
        phase=StructurePhase.BLOCKED,
        reasons=("test_closed",),
    )
    inspect = MagicMock()
    flows = FlowExecutionService(
        commands=CommandBus(),
        queries=QueryBus(),
        schemas=MagicMock(),
        inspect=inspect,
        admission_source=lambda: closed,
    )
    flows.resolve_runtime = MagicMock(  # type: ignore[method-assign]
        side_effect=AssertionError("published admission broken: resolve_runtime used for admission")
    )
    flows.dispatch_command = MagicMock(  # type: ignore[method-assign]
        side_effect=AssertionError("must not dispatch when admission closed")
    )
    return flows


def test_submit_flow_body_refused_on_oath_without_runtime_dig() -> None:
    flows = _flows_with_closed_inject()
    with pytest.raises(AdmissionRefusedError, match="test_closed"):
        flows.submit_flow_body({"flow_name": "todo-builder"})
    flows.resolve_runtime.assert_not_called()
    flows.dispatch_command.assert_not_called()


def test_run_wizard_refused_on_oath() -> None:
    flows = _flows_with_closed_inject()
    with pytest.raises(AdmissionRefusedError, match="test_closed"):
        flows.run_wizard({"flow_name": "todo-builder"})
    flows.dispatch_command.assert_not_called()


def test_run_flow_refused_on_oath() -> None:
    flows = _flows_with_closed_inject()
    with pytest.raises(AdmissionRefusedError, match="test_closed"):
        flows.run_flow("todo-builder")
    flows.dispatch_command.assert_not_called()


def test_host_flows_start_refused_when_assembly_skipped() -> None:
    reset_system_log_for_tests()
    host = ApplicationHost.for_mode("all_in_one", settings=_settings())
    host.start(structure_skip=True)
    try:
        assert host.admission.may_run_business is False
        with pytest.raises(AdmissionRefusedError):
            host.execution.flows.submit_flow_body({"flow_name": "todo-builder"})
        with pytest.raises(AdmissionRefusedError):
            host.execution.flows.run_flow("todo-builder")
    finally:
        host.shutdown()


def test_inventory_flows_start_and_soft_catalog() -> None:
    gated = {row["id"] for row in GATED_PATHS}
    assert "flows.start_session" in gated
    pretenders = {row["id"]: row["status"] for row in READINESS_EDGES}
    assert pretenders["flows.start_edge"] == "paid_0_63_32"
    assert pretenders["flows.soft_catalog"] == "named_0_63_32"
    assert admission_inventory()["gated_count"] >= 1
