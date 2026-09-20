"""0.71.11 — invert StructureEngine place observations off a second body book.

Assemble readiness reads the place registry via a typed ready hand.
PLACE_READY does not accumulate a second places set when that hand is bound.
Bound bare / os: assemble acks live on the registry local register; places
stays book projection only (0.71.9).
"""

from __future__ import annotations

from pathlib import Path

from palm.core.structure import (
    EffectIntent,
    EffectIntentKind,
    Observation,
    ObservationKind,
    StructureDefinition,
    StructureEngine,
    StructurePhase,
)
from palm.core.workload import WorkloadEngine, WorkloadHandle, WorkloadStatus
from palm.system.structure import (
    PlaceEffectPort,
    StructureSeat,
    combined_structure_spawn_port,
)
from palm.system.structure.place_registry import InProcessPlaceRegistry
from palm.system.structure.workload_place import adopt_prefix_spawn_port

_CORE_ENGINE = (
    Path(__file__).resolve().parents[1]
    / "src"
    / "palm"
    / "core"
    / "structure"
    / "engine.py"
)
_PLACE_REGISTRY = (
    Path(__file__).resolve().parents[1]
    / "src"
    / "palm"
    / "system"
    / "structure"
    / "place_registry.py"
)


def _engine() -> WorkloadEngine:
    eng = WorkloadEngine()
    eng.initialize()
    return eng


def test_registry_ready_checks_local_and_book() -> None:
    reg = InProcessPlaceRegistry()
    assert hasattr(reg, "ready")
    assert reg.ready("support_home") is False
    reg.mark("support_home", "ready")
    assert reg.ready("support_home") is True
    assert reg.places.get("support_home") == "ready"


def test_bound_bare_ready_on_registry_not_places_projection() -> None:
    eng = _engine()
    try:
        port = PlaceEffectPort(spawn=combined_structure_spawn_port(engine=eng))
        obs = port.apply(
            EffectIntent(kind=EffectIntentKind.ENSURE_PLACE, target="support_home")
        )
        assert obs[0].kind is ObservationKind.PLACE_READY
        assert port.registry.ready("support_home") is True
        assert "support_home" not in port.registry.places
        assert "support_home" not in {wl.workload_id for wl in eng.list()}
    finally:
        eng.shutdown()


def test_engine_with_ready_hand_does_not_fold_place_ready_into_local_set() -> None:
    ready_ids = {"support_home"}
    eng = StructureEngine()
    eng.initialize()
    eng.bind_place_ready(lambda place_id: place_id in ready_ids)
    dna = StructureDefinition(
        id="local.with_place",
        version="1",
        places_required=("support_home",),
    )
    eng.receive_definition(dna)
    eng.observe(
        Observation(kind=ObservationKind.PLACE_READY, target="support_home")
    )
    assert eng._places_ready == set()  # noqa: SLF001 — invert proof
    result = eng.tick()
    assert result.admission.may_run_business is True
    assert result.status.places_ready == frozenset({"support_home"})


def test_engine_without_hand_still_folds_observations_for_pure_tests() -> None:
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
    assert "support_home" in eng._places_ready  # noqa: SLF001
    result = eng.tick()
    assert result.admission.may_run_business is True


def test_seat_assemble_reads_registry_ready_not_second_book() -> None:
    seat = StructureSeat()
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
    assert seat.effects.registry.ready("support_home") is True  # type: ignore[union-attr]
    assert seat.effects.registry.ready("work_yard") is True  # type: ignore[union-attr]
    assert seat.engine._places_ready == set()  # noqa: SLF001 — hand bound


def test_seat_adopt_converges_from_book_via_ready_hand() -> None:
    eng = _engine()
    try:
        eng.adopt(
            "adopt:manor",
            WorkloadHandle(workload_id="adopt:manor", base_url="http://127.0.0.1:11"),
        )
        seat = StructureSeat(
            effects=PlaceEffectPort(spawn=adopt_prefix_spawn_port(engine=eng))
        )
        dna = StructureDefinition(
            id="local.with_adopted_place",
            places_required=("adopt:manor",),
        )
        seat.assemble(dna)
        assert seat.admission().may_run_business is True
        assert seat.effects.registry.ready("adopt:manor") is True  # type: ignore[union-attr]
        assert seat.effects.registry.places.get("adopt:manor") == "ready"  # type: ignore[union-attr]
        assert seat.engine._places_ready == set()  # noqa: SLF001
    finally:
        eng.shutdown()


def test_adopt_stop_drops_ready_via_registry_hand() -> None:
    eng = _engine()
    try:
        eng.adopt(
            "adopt:yard",
            WorkloadHandle(workload_id="adopt:yard", base_url="http://127.0.0.1:9"),
        )
        port = PlaceEffectPort(spawn=adopt_prefix_spawn_port(engine=eng))
        seat = StructureSeat(effects=port)
        dna = StructureDefinition(
            id="local.adopt_unbind",
            places_required=("adopt:yard",),
        )
        seat.assemble(dna)
        assert seat.admission().may_run_business is True
        eng.stop("adopt:yard")
        assert eng.get("adopt:yard").status is WorkloadStatus.STOPPED
        assert port.registry.ready("adopt:yard") is False
        assert "adopt:yard" not in port.registry.places
        seat.engine.invalidate()
        loop = seat.assemble(dna, force=True)
        assert loop.steady is True
        # stop left the row terminal; adopt ensure without handle fails closed
        assert seat.admission().may_run_business is False
        assert seat.admission().phase is StructurePhase.BLOCKED
    finally:
        eng.shutdown()


def test_bound_os_ready_lives_on_registry_ready() -> None:
    eng = _engine()
    try:
        port = PlaceEffectPort(spawn=combined_structure_spawn_port(engine=eng))
        obs = port.apply(
            EffectIntent(
                kind=EffectIntentKind.ENSURE_PLACE,
                target="os:worker-a",
                payload={"handle": "pid-9"},
            )
        )
        assert obs[0].kind is ObservationKind.PLACE_READY
        assert port.registry.ready("os:worker-a") is True
        assert "os:worker-a" not in port.registry.places
    finally:
        eng.shutdown()


def test_structure_sources_prefer_registry_ready_hand() -> None:
    engine_text = _CORE_ENGINE.read_text(encoding="utf-8")
    assert "bind_place_ready" in engine_text
    assert "_place_ready" in engine_text
    registry_text = _PLACE_REGISTRY.read_text(encoding="utf-8")
    assert "def ready(" in registry_text
