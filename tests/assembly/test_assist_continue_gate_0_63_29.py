"""0.63.29 — assist product continue doors are business paths that need admission; cancel named residual."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from bundles.standard.app.host.application_host import ApplicationHost
from bundles.standard.app.settings import PalmSettings
from palm.core.structure import AdmissionSnapshot, StructurePhase
from palm.services.assist.session import AssistSession
from palm.system.log import reset_system_log_for_tests
from palm.system.runtime.base import BaseRuntime
from palm.system.structure.errors import AdmissionRefusedError
from palm.system.structure.inventory import GATED_PATHS, READINESS_EDGES, admission_inventory


def _settings() -> PalmSettings:
    return PalmSettings(
        load_example_definitions=True,
        storage_backend="memory",
        rebuild_projections_on_startup=False,
        reconcile_instances_on_startup=False,
    )


def _closed_assist() -> MagicMock:
    closed = AdmissionSnapshot(
        may_run_business=False,
        phase=StructurePhase.BLOCKED,
        reasons=("test_closed",),
    )
    assist = MagicMock()
    assist.admission_gate.return_value = closed
    assist.resolve_runtime.side_effect = AssertionError(
        "published admission broken: resolve_runtime used for admission"
    )
    return assist


def test_assist_session_input_refused_on_oath_without_runtime_dig() -> None:
    assist = _closed_assist()
    session = AssistSession(assist, flow_id="f", session_id="inst-1")
    with pytest.raises(AdmissionRefusedError, match="test_closed"):
        session.input("x")
    assist.resolve_runtime.assert_not_called()


def test_assist_session_resume_refused_on_oath() -> None:
    assist = _closed_assist()
    session = AssistSession(assist, flow_id="f", session_id="inst-1")
    with pytest.raises(AdmissionRefusedError, match="test_closed"):
        session.resume()


def test_assist_session_backtrack_refused_on_oath() -> None:
    assist = _closed_assist()
    session = AssistSession(assist, flow_id="f", session_id="inst-1")
    with pytest.raises(AdmissionRefusedError, match="test_closed"):
        session.backtrack()


def test_assist_session_cancel_not_admission_citizen() -> None:
    """Cancel stays control path when admission is closed (named residual)."""
    assist = _closed_assist()
    flow = MagicMock()
    flow.cancel.return_value = {"cancelled": True}
    assist.execution.flows.session.return_value = flow
    session = AssistSession(assist, flow_id="f", session_id="inst-1")
    assert session.cancel() == {"cancelled": True}
    flow.cancel.assert_called_once()


def test_host_assist_continue_refused_when_assembly_skipped() -> None:
    """Live packaging inject: host assist continue uses admission_gate, not dig."""
    reset_system_log_for_tests()
    host = ApplicationHost.for_mode("all_in_one", settings=_settings())
    host.start(structure_skip=True)
    try:
        assert host.assist is not None
        assert host.admission.may_run_business is False
        # Handle without inspect (no live instance) — gate is on continue verbs.
        session = AssistSession(host.assist, flow_id="f", session_id="inst-x")
        with pytest.raises(AdmissionRefusedError):
            session.resume()
        with pytest.raises(AdmissionRefusedError):
            session.input("x")
        with pytest.raises(AdmissionRefusedError):
            session.backtrack()
    finally:
        host.shutdown()


def test_resume_process_refused_when_assembly_skipped() -> None:
    """Cartography: resume_process already gated via executor._require_runtime."""
    reset_system_log_for_tests()
    rt = BaseRuntime()
    rt.start(
        storage_backend="memory",
        structure_skip=True,
    )
    try:
        assert rt.admission.may_run_business is False
        with pytest.raises(AdmissionRefusedError):
            rt.resume_process("instance-missing")
    finally:
        rt.stop()


def test_inventory_assist_continue_and_resume_process() -> None:
    gated = {row["id"] for row in GATED_PATHS}
    assert "assist.continue_session" in gated
    assert "executor.resume_process" in gated
    pretenders = {row["id"]: row["status"] for row in READINESS_EDGES}
    assert pretenders["assist.session_cancel_ungated"] == "named_0_63_29"
    assert pretenders["assist.continue_edge"] == "paid_0_63_29"
    assert admission_inventory()["gated_count"] >= 1
