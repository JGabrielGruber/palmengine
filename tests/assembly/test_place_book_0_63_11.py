"""0.63.11 — in-process place registry hands for ENSURE_PLACE."""

from __future__ import annotations

from palm.core.structure import (
    EffectIntent,
    EffectIntentKind,
    StructureDefinition,
    StructurePhase,
)
from palm.system.log import reset_system_log_for_tests
from palm.system.runtime.base import BaseRuntime
from palm.system.structure import (
    InProcessPlaceRegistry,
    PlaceEffectPort,
    StructureSeat,
)


def test_place_registry_ensure_release() -> None:
    registry = InProcessPlaceRegistry()
    port = PlaceEffectPort(registry=registry)
    obs = port.apply(
        EffectIntent(kind=EffectIntentKind.ENSURE_PLACE, target="support_home")
    )
    assert obs[0].kind.value == "place_ready"
    assert registry.places["support_home"] == "ready"
    obs2 = port.apply(
        EffectIntent(kind=EffectIntentKind.RELEASE_PLACE, target="support_home")
    )
    assert obs2[0].kind.value == "place_gone"
    assert "support_home" not in registry.places


def test_seat_assemble_with_places_converges() -> None:
    seat = StructureSeat()  # default StructureEffectPort (0.63.15)
    dna = StructureDefinition(
        id="local.with_places",
        version="1",
        places_required=("support_home", "work_yard"),
    )
    loop = seat.assemble(dna)
    assert loop.steady is True
    assert seat.admission().may_run_business is True
    assert seat.admission().phase is StructurePhase.READY
    assert seat.status().places_ready == frozenset({"support_home", "work_yard"})
    assert set(seat.effects.registry.places) == {"support_home", "work_yard"}  # type: ignore[union-attr]


def test_runtime_default_place_registry_hands() -> None:
    reset_system_log_for_tests()
    rt = BaseRuntime()
    rt.start(
        storage_backend="memory",
        structure_definition=StructureDefinition(
            id="local.with_place",
            places_required=("manor_a",),
        ),
    )
    try:
        assert rt.admission.may_run_business is True
        assert rt.structure is not None
        # Bound book: registry.places is body projection; bare ready is assemble observation.
        assert "manor_a" in rt.structure.status().places_ready
    finally:
        rt.stop()
