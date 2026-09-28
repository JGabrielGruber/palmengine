"""0.63.20 — product workload start is a business path that needs admission (fail closed)."""

from __future__ import annotations

import pytest

from palm.core.workload import (
    IsolationPolicy,
    LifecyclePolicy,
    WorkloadKind,
    WorkloadSpec,
)
from palm.system.log import reset_system_log_for_tests
from palm.system.runtime.base import BaseRuntime
from palm.system.structure.errors import AdmissionRefusedError
from tests.helpers.bound import bound_for_runtime


def _minimal_spec() -> WorkloadSpec:
    # Valid shape; packaging may still refuse host runtime — admission is separate.
    return WorkloadSpec(
        kind=WorkloadKind.WORKSPACE,
        isolation=IsolationPolicy.HOST,
        lifecycle=LifecyclePolicy.JOB,
    )


def test_start_workload_refused_when_assembly_skipped() -> None:
    reset_system_log_for_tests()
    rt = BaseRuntime()
    rt.start(
        drivers=bound_for_runtime(storage_backend="memory"),
        structure_skip=True,
        workload_host_enabled=True,
    )
    try:
        assert rt.admission.may_run_business is False
        # Spec not needed — admission fails closed first.
        with pytest.raises(AdmissionRefusedError):
            rt.start_workload({"kind": "workspace"})  # type: ignore[arg-type]
    finally:
        rt.stop()


def test_start_workload_refused_when_dna_refuse_blocks() -> None:
    """Embedded DNA + server surfaces → admission blocked → no product start."""
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
            rt.start_workload({"kind": "workspace"})  # type: ignore[arg-type]
    finally:
        rt.stop()


def test_start_workload_allowed_when_admitted() -> None:
    reset_system_log_for_tests()
    rt = BaseRuntime()
    rt.start(drivers=bound_for_runtime(storage_backend="memory"), workload_host_enabled=True)
    try:
        assert rt.admission.may_run_business is True
        # Host runtime may fail for other reasons; admission must not refuse first.
        try:
            wl = rt.start_workload(_minimal_spec())
            assert wl is not None
        except Exception as exc:
            # Not admission — engine/runtime packaging failures are ok for this wall.
            assert not isinstance(exc, AdmissionRefusedError)
            assert "Admission" not in type(exc).__name__
    finally:
        rt.stop()


def test_structure_workload_engine_not_gated_by_port() -> None:
    """Place-book path uses engine directly — unit path, not ExecutionPort admission path."""
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
        # Direct engine start is place-registry / unit path; does not call require_business_admission.
        # May still fail on host runtime packaging — only assert no AdmissionRefusedError.
        try:
            engine.start(_minimal_spec())
        except Exception as exc:
            assert not isinstance(exc, AdmissionRefusedError)
    finally:
        rt.stop()
