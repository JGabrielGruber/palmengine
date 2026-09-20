"""0.71.14 — invert seat assemble bind_structure off getattr duck-walk.

StructureSeat.assemble binds definition/surfaces via typed StructureEffectPort.
No getattr(self.effects, "bind_structure", None). PlaceEffectPort /
RecordingEffectPort assemble without a bind_structure hand.
"""

from __future__ import annotations

from pathlib import Path

from palm.core.structure import StructureDefinition, local_embedded
from palm.system.structure import (
    PlaceEffectPort,
    RecordingEffectPort,
    StructureEffectPort,
    StructureSeat,
)

_SEAT = (
    Path(__file__).resolve().parents[1]
    / "src"
    / "palm"
    / "system"
    / "structure"
    / "seat.py"
)


def test_seat_source_has_no_bind_structure_getattr() -> None:
    text = _SEAT.read_text(encoding="utf-8")
    assert 'getattr(self.effects, "bind_structure"' not in text
    assert 'getattr(self.effects, "bind_structure", None)' not in text


def test_assemble_binds_structure_effect_port() -> None:
    port = StructureEffectPort()
    seat = StructureSeat(effects=port)
    dna = StructureDefinition(id="local.bind", version="1")
    surfaces = ("cli", "mcp")
    seat.assemble(dna, surfaces=surfaces)
    assert port.definition is dna
    assert port.surfaces == ("cli", "mcp")


def test_assemble_default_effects_bind_embedded() -> None:
    seat = StructureSeat()
    assert isinstance(seat.effects, StructureEffectPort)
    seat.assemble()
    assert seat.effects.definition is not None
    assert seat.effects.definition.id == local_embedded().id


def test_assemble_place_effect_port_needs_no_bind_structure() -> None:
    port = PlaceEffectPort()
    assert not hasattr(port, "bind_structure")
    seat = StructureSeat(effects=port)
    dna = StructureDefinition(id="local.places_only", version="1")
    loop = seat.assemble(dna)
    assert loop.steady is True
    assert seat.definition is dna


def test_assemble_recording_effect_port_needs_no_bind_structure() -> None:
    port = RecordingEffectPort(auto_ack_places=True)
    assert not hasattr(port, "bind_structure")
    seat = StructureSeat(effects=port)
    dna = StructureDefinition(
        id="local.recording",
        version="1",
        places_required=("support_home",),
    )
    loop = seat.assemble(dna)
    assert loop.steady is True
    assert seat.definition is dna
