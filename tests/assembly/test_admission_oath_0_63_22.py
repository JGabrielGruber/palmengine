"""0.63.22 — published admission: inject, not runtime dig for readiness."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from palm.core.structure import AdmissionSnapshot, StructurePhase, local_embedded
from palm.system.structure import (
    AdmissionRefusedError,
    StructureSeat,
    coerce_admission_snapshot,
    require_business_admission,
)
from palm.system.structure.inventory import GATED_PATHS, admission_inventory


def test_coerce_snapshot_direct() -> None:
    seat = StructureSeat()
    seat.assemble(local_embedded())
    ready = seat.admission()
    assert coerce_admission_snapshot(ready) is ready
    assert require_business_admission(ready).may_run_business is True


def test_coerce_zero_arg_factory() -> None:
    seat = StructureSeat()
    seat.assemble(local_embedded())
    snap = require_business_admission(lambda: seat.admission())
    assert snap.may_run_business is True


def test_coerce_factory_refused() -> None:
    closed = AdmissionSnapshot.empty()
    with pytest.raises(AdmissionRefusedError):
        require_business_admission(lambda: closed)


def test_assist_admission_gate_prefers_inject_over_runtime() -> None:
    """Business path that needs admission must use injected source — never require resolve_runtime."""
    from services.assist.service import AssistService

    closed = AdmissionSnapshot(
        may_run_business=False,
        phase=StructurePhase.BLOCKED,
        reasons=("test_closed",),
    )
    assist = MagicMock(spec=AssistService)
    assist.admission_gate.return_value = closed
    assist.resolve_runtime.side_effect = AssertionError(
        "published admission broken: resolve_runtime used for admission"
    )
    with pytest.raises(AdmissionRefusedError, match="test_closed"):
        require_business_admission(assist.admission_gate())
    assist.resolve_runtime.assert_not_called()


def test_assist_service_admission_gate_uses_source() -> None:
    """AssistService.admission_gate returns inject; fallback is only when unset."""
    from palm.common.cqrs.bus import CommandBus, QueryBus
    from services.assist.service import AssistService

    ready = AdmissionSnapshot(
        may_run_business=True,
        phase=StructurePhase.READY,
        definition_id="test",
    )
    inspect = MagicMock()
    definitions = MagicMock()
    execution = MagicMock()
    # Minimal construct — bus kwargs required by BaseService
    svc = AssistService(
        commands=CommandBus(),
        queries=QueryBus(),
        schemas=MagicMock(),
        definitions=definitions,
        execution=execution,
        inspect=inspect,
        admission_source=lambda: ready,
    )
    # Must not dig execution.flows for gate
    execution.flows.resolve_runtime.side_effect = AssertionError("no dig")
    gate = svc.admission_gate()
    assert require_business_admission(gate).definition_id == "test"
    execution.flows.resolve_runtime.assert_not_called()


def test_inventory_marks_published_admission() -> None:
    ids = {c["id"] for c in GATED_PATHS}
    assert "assist.published_admission" in ids
    body = admission_inventory()
    assert any(c["id"] == "assist.published_admission" for c in body["gated_paths"])
