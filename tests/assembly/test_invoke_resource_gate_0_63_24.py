"""0.63.24 — product resource invoke is a business path that needs admission (fail closed)."""

from __future__ import annotations

import pytest

from palm.system.log import reset_system_log_for_tests
from palm.system.runtime.base import BaseRuntime
from palm.system.structure.errors import AdmissionRefusedError
from palm.system.structure.inventory import GATED_PATHS, admission_inventory
from tests.helpers.bound import bound_for_runtime


def test_invoke_resource_refused_when_assembly_skipped() -> None:
    reset_system_log_for_tests()
    rt = BaseRuntime()
    rt.start(drivers=bound_for_runtime(storage_backend="memory"), structure_skip=True)
    try:
        assert rt.admission.may_run_business is False
        with pytest.raises(AdmissionRefusedError):
            rt.invoke_resource("any-ref", action="get")
    finally:
        rt.stop()


def test_invoke_resource_refused_when_dna_refuse_blocks() -> None:
    """Embedded DNA + server surfaces → admission blocked → no product invoke."""
    reset_system_log_for_tests()
    rt = BaseRuntime()
    rt.start(
        drivers=bound_for_runtime(storage_backend="memory"),
        structure_definition_id="local.embedded",
        structure_surfaces=["rest"],
    )
    try:
        assert rt.admission.may_run_business is False
        with pytest.raises(AdmissionRefusedError):
            rt.invoke_resource("any-ref", action="get")
    finally:
        rt.stop()


def test_invoke_resource_allowed_when_admitted() -> None:
    reset_system_log_for_tests()
    rt = BaseRuntime()
    rt.start(drivers=bound_for_runtime(storage_backend="memory"))
    try:
        assert rt.admission.may_run_business is True
        # Definition/provider may fail for other reasons; admission must not refuse first.
        try:
            rt.invoke_resource("nonexistent-resource-ref", action="get")
        except Exception as exc:
            assert not isinstance(exc, AdmissionRefusedError)
            assert "Admission" not in type(exc).__name__
    finally:
        rt.stop()


def test_structure_resource_engine_not_gated_by_port() -> None:
    """Direct ResourceEngine.invoke is not the ExecutionPort admission door."""
    reset_system_log_for_tests()
    rt = BaseRuntime()
    rt.start(drivers=bound_for_runtime(storage_backend="memory"), structure_skip=True)
    try:
        engine = rt.resource
        assert engine is not None
        if not engine.is_initialized:
            engine.initialize()
        try:
            engine.invoke("any-ref", action="get")
        except Exception as exc:
            assert not isinstance(exc, AdmissionRefusedError)
    finally:
        rt.stop()


def test_inventory_lists_invoke_resource_citizen() -> None:
    ids = {row["id"] for row in GATED_PATHS}
    assert "execution.invoke_resource" in ids
    assert admission_inventory()["gated_count"] >= len(GATED_PATHS)
