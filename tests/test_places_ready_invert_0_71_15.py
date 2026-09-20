"""0.71.15 — invert StructureEngine `_places_ready` dual.

Place readiness lives only behind the bound ready hand. No second set.
Unbound hand: PLACE_READY does not accumulate readiness (fail closed).
RecordingEffectPort auto-ack owns a ready hand the seat binds.
"""

from __future__ import annotations

from pathlib import Path

from palm.core.structure import (
    Observation,
    ObservationKind,
    StructureDefinition,
    StructureEngine,
    StructurePhase,
)
from palm.system.structure import RecordingEffectPort, StructureSeat

_CORE_ENGINE = (
    Path(__file__).resolve().parents[1]
    / "src"
    / "palm"
    / "core"
    / "structure"
    / "engine.py"
)
_SEAT = (
    Path(__file__).resolve().parents[1]
    / "src"
    / "palm"
    / "system"
    / "structure"
    / "seat.py"
)
_EFFECTS = (
    Path(__file__).resolve().parents[1]
    / "src"
    / "palm"
    / "system"
    / "structure"
    / "effects.py"
)


def test_engine_source_has_no_places_ready_set() -> None:
    text = _CORE_ENGINE.read_text(encoding="utf-8")
    assert "_places_ready: set" not in text
    assert "self._places_ready.add" not in text
    assert "self._places_ready.clear" not in text
    assert "self._places_ready.discard" not in text
    assert "in self._places_ready" not in text
    assert "frozenset(self._places_ready)" not in text
    assert "bind_place_ready" in text
    assert "_place_ready" in text


def test_unbound_hand_place_ready_observation_does_not_admit() -> None:
    eng = StructureEngine()
    eng.initialize()
    dna = StructureDefinition(
        id="local.with_place",
        version="1",
        places_required=("support_home",),
    )
    eng.receive_definition(dna)
    eng.tick()
    eng.observe(
        Observation(kind=ObservationKind.PLACE_READY, target="support_home")
    )
    result = eng.tick()
    assert result.admission.may_run_business is False
    assert result.admission.phase is StructurePhase.ASSEMBLING
    assert "support_home" in result.status.places_missing
    assert result.status.places_ready == frozenset()
    assert not hasattr(eng, "_places_ready")


def test_bound_hand_is_sole_readiness_truth() -> None:
    ready_ids: set[str] = set()
    eng = StructureEngine()
    eng.initialize()
    eng.bind_place_ready(lambda place_id: place_id in ready_ids)
    dna = StructureDefinition(
        id="local.with_place",
        version="1",
        places_required=("support_home",),
    )
    eng.receive_definition(dna)
    eng.tick()
    eng.observe(
        Observation(kind=ObservationKind.PLACE_READY, target="support_home")
    )
    assert eng.tick().admission.may_run_business is False
    ready_ids.add("support_home")
    eng.observe(
        Observation(kind=ObservationKind.PLACE_READY, target="support_home")
    )
    result = eng.tick()
    assert result.admission.may_run_business is True
    assert result.status.places_ready == frozenset({"support_home"})
    assert not hasattr(eng, "_places_ready")


def test_recording_port_ready_hand_admits_auto_ack() -> None:
    port = RecordingEffectPort(auto_ack_places=True)
    assert hasattr(port, "ready")
    assert port.ready("support_home") is False
    seat = StructureSeat(effects=port)
    dna = StructureDefinition(
        id="local.recording",
        version="1",
        places_required=("support_home",),
    )
    loop = seat.assemble(dna)
    assert loop.steady is True
    assert seat.admission().may_run_business is True
    assert port.ready("support_home") is True
    assert seat.status().places_ready == frozenset({"support_home"})
    assert not hasattr(seat.engine, "_places_ready")


def test_seat_and_recording_sources_bind_ready_hand() -> None:
    seat_text = _SEAT.read_text(encoding="utf-8")
    assert "RecordingEffectPort" in seat_text
    assert "bind_place_ready" in seat_text
    effects_text = _EFFECTS.read_text(encoding="utf-8")
    assert "def ready(" in effects_text
