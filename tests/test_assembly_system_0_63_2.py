"""0.63.2 — system assembly seat + structure assemble phase."""

from __future__ import annotations

from palm.core.structure import (
    LOCAL_EMBEDDED_ID,
    StructureDefinition,
    StructurePhase,
    local_embedded,
)
from palm.system.boot import system_phase_ids
from palm.system.log import reset_system_log_for_tests
from palm.system.runtime.base import BaseRuntime
from palm.system.structure import (
    RecordingEffectPort,
    StructureSeat,
    assemble_until_steady,
    load_and_assemble,
)
from tests.helpers.bound import bound_for_runtime


def test_system_phase_table_includes_assembly() -> None:
    ids = system_phase_ids()
    assert "system.structure.assemble" in ids
    assert ids.index("system.ready") < ids.index("system.structure.assemble")
    assert ids.index("system.structure.assemble") < ids.index("system.background.start")


def test_load_and_assemble_embedded_ready() -> None:
    seat = StructureSeat()
    loop = seat.assemble(local_embedded())
    assert loop.steady is True
    assert loop.last.admission.may_run_business is True
    assert loop.last.admission.definition_id == LOCAL_EMBEDDED_ID
    assert seat.admission().phase is StructurePhase.READY


def test_assemble_with_places_auto_ack() -> None:
    seat = StructureSeat(effects=RecordingEffectPort(auto_ack_places=True))
    dna = StructureDefinition(
        id="local.with_place",
        version="1",
        places_required=("support_home",),
    )
    loop = seat.assemble(dna)
    assert loop.steady is True
    assert seat.admission().may_run_business is True
    assert any(
        i.target == "support_home"
        for i in seat.effects.applied  # type: ignore[attr-defined]
    )


def test_runtime_start_publishes_admission() -> None:
    reset_system_log_for_tests()
    rt = BaseRuntime()
    rt.start(drivers=bound_for_runtime(storage_backend="memory"))
    try:
        assert rt.is_started
        by_id = {w.phase: w for w in (rt._last_boot_walk or [])}
        assert by_id["system.structure.assemble"].outcome == "ok"
        assert rt.structure is not None
        snap = rt.admission
        assert snap.may_run_business is True
        assert snap.definition_id == LOCAL_EMBEDDED_ID
        assert snap.phase is StructurePhase.READY
    finally:
        rt.stop()
        assert rt.structure is None
        assert rt.admission.may_run_business is False


def test_runtime_assembly_skip_fail_closed() -> None:
    reset_system_log_for_tests()
    rt = BaseRuntime()
    rt.start(drivers=bound_for_runtime(storage_backend="memory"), structure_skip=True)
    try:
        by_id = {w.phase: w for w in (rt._last_boot_walk or [])}
        assert by_id["system.structure.assemble"].outcome == "skip"
        assert by_id["system.structure.assemble"].reason == "structure_skip"
        assert rt.structure is None
        assert rt.admission.may_run_business is False
        assert rt.admission.phase is StructurePhase.EMPTY
    finally:
        rt.stop()


def test_runtime_custom_dna_id() -> None:
    reset_system_log_for_tests()
    rt = BaseRuntime()
    rt.start(
        drivers=bound_for_runtime(storage_backend="memory"),
        structure_definition_id="local.embedded",
        structure_definition_version="9",
    )
    try:
        assert rt.admission.definition_version == "9"
        assert rt.admission.may_run_business is True
    finally:
        rt.stop()


def test_loop_module_export() -> None:
    engine = StructureSeat().engine
    effects = RecordingEffectPort()
    result = load_and_assemble(engine, effects, local_embedded())
    assert result.last.admission.may_run_business is True
    again = assemble_until_steady(engine, effects)
    assert again.last.admission.may_run_business is True
