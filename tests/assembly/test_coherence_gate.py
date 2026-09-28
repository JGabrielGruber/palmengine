"""Coherence suite — fail-closed admission (truth instrument).

These tests assert Palm does **not** start business when admission is down.
Green means single truth on owned paths; soft-open is dual mode.
"""

from __future__ import annotations

import pytest

from palm.core.structure import (
    Observation,
    ObservationKind,
    StructurePhase,
    local_embedded,
)
from palm.core.work import WorkIntent
from palm.definitions.flow import FlowDefinition
from palm.system.log import reset_system_log_for_tests
from palm.system.runtime.base import BaseRuntime
from palm.system.structure import (
    AdmissionRefusedError,
    StructureSeat,
    require_business_admission,
)
from tests.helpers.bound import bound_for_runtime


def _noop_flow() -> FlowDefinition:
    return FlowDefinition(
        name="coherence-noop",
        pattern="wizard",
        options={"steps": [{"slug": "a", "title": "A", "prompt": "?"}]},
    )


def test_require_admission_empty_raises() -> None:
    class _NoSnap:
        is_started = True

    with pytest.raises(AdmissionRefusedError):
        require_business_admission(_NoSnap())


def test_require_admission_ready_ok() -> None:
    seat = StructureSeat()
    seat.assemble(local_embedded())
    assert seat.admission().may_run_business is True

    class _Shell:
        admission = seat.admission()

    snap = require_business_admission(_Shell())
    assert snap.may_run_business is True


def test_require_admission_accepts_snapshot_and_factory() -> None:
    """0.63.22 — published admission shapes, not only runtime shells."""
    seat = StructureSeat()
    seat.assemble(local_embedded())
    ready = seat.admission()
    assert require_business_admission(ready).may_run_business is True
    assert require_business_admission(lambda: ready).may_run_business is True


def test_submit_flow_fail_closed_when_assembly_skipped() -> None:
    reset_system_log_for_tests()
    rt = BaseRuntime()
    rt.start(drivers=bound_for_runtime(storage_backend="memory"), structure_skip=True)
    try:
        assert rt.admission.may_run_business is False
        with pytest.raises(AdmissionRefusedError, match="admission refused"):
            rt.submit_flow(_noop_flow())
    finally:
        rt.stop()


def test_submit_flow_ok_when_embedded_ready() -> None:
    reset_system_log_for_tests()
    rt = BaseRuntime()
    rt.start(drivers=bound_for_runtime(storage_backend="memory"))
    try:
        assert rt.admission.may_run_business is True
        job = rt.submit_flow(_noop_flow())
        assert job is not None
        assert job.metadata.get("flow") == "coherence-noop"
    finally:
        rt.stop()


def test_submit_fail_closed_truth_home_down() -> None:
    reset_system_log_for_tests()
    rt = BaseRuntime()
    rt.start(drivers=bound_for_runtime(storage_backend="memory"))
    try:
        assert rt.structure is not None
        rt.structure.engine.observe(Observation(kind=ObservationKind.TRUTH_HOME_DOWN))
        assert rt.admission.may_run_business is False
        with pytest.raises(AdmissionRefusedError):
            rt.submit_flow(_noop_flow())
    finally:
        rt.stop()


def test_work_plane_and_submit_same_gate() -> None:
    """Both business paths that need admission refuse under the same snapshot."""
    reset_system_log_for_tests()
    rt = BaseRuntime()
    rt.start(drivers=bound_for_runtime(storage_backend="memory"), structure_skip=True)
    try:
        plane = rt.work_plane
        assert plane is not None
        assert plane.is_able() is False
        plane.enqueue(WorkIntent(kind="run_flow", target="x"))
        assert plane.tick(limit=5) == 0
        with pytest.raises(AdmissionRefusedError):
            rt.submit_flow(_noop_flow())
        assert rt.admission.phase is StructurePhase.EMPTY
    finally:
        rt.stop()
