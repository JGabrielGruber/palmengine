"""0.63.16 — workload: place spawn against WorkloadEngine."""

from __future__ import annotations

import sys

from palm.core.structure import (
    EffectIntent,
    EffectIntentKind,
    StructureDefinition,
    StructurePhase,
)
from palm.core.workload import WorkloadEngine
from plugins.runners.local.runtime import LocalWorkloadRuntime
from palm.system.structure import (
    PlaceEffectPort,
    StructureSeat,
    WorkloadPlaceSpawn,
    combined_structure_spawn_port,
    workload_prefix_spawn_port,
)


def _engine_with_local() -> WorkloadEngine:
    eng = WorkloadEngine()
    eng.initialize(
        default_runtime="local",
        runtimes={"local": LocalWorkloadRuntime(name="local")},
    )
    return eng


def test_workload_fail_closed_without_engine() -> None:
    hands = WorkloadPlaceSpawn(engine=None)
    result = hands.ensure("workload:yard", {})
    assert result.state == "failed"
    assert result.reason == "workload_engine_not_bound"


def test_workload_workspace_place_ready() -> None:
    eng = _engine_with_local()
    try:
        spawn = workload_prefix_spawn_port(engine=eng)
        port = PlaceEffectPort(spawn=spawn)
        obs = port.apply(
            EffectIntent(
                kind=EffectIntentKind.ENSURE_PLACE,
                target="workload:support",
            )
        )
        assert obs[0].kind.value == "place_ready"
        assert obs[0].payload.get("spawn") == "workload_started"
        assert "workload:support" in port.registry.places
        # release
        gone = port.apply(
            EffectIntent(
                kind=EffectIntentKind.RELEASE_PLACE,
                target="workload:support",
            )
        )
        assert gone[0].kind.value == "place_gone"
    finally:
        eng.shutdown()


def test_workload_run_place_with_command() -> None:
    eng = _engine_with_local()
    try:
        hands = WorkloadPlaceSpawn(engine=eng)
        result = hands.ensure(
            "workload:job-a",
            {
                "kind": "run",
                "argv": [sys.executable, "-c", "print('ok')"],
            },
        )
        assert result.state == "ready"
        assert result.reason == "workload_started"
    finally:
        eng.shutdown()


def test_seat_workload_place_converges() -> None:
    eng = _engine_with_local()
    try:
        seat = StructureSeat(
            effects=PlaceEffectPort(spawn=workload_prefix_spawn_port(engine=eng))
        )
        dna = StructureDefinition(
            id="local.with_workload_place",
            places_required=("workload:manor",),
        )
        seat.assemble(dna)
        assert seat.admission().may_run_business is True
        assert seat.admission().phase is StructurePhase.READY
    finally:
        eng.shutdown()


def test_seat_workload_unbound_blocks() -> None:
    seat = StructureSeat(
        effects=PlaceEffectPort(spawn=workload_prefix_spawn_port(engine=None))
    )
    dna = StructureDefinition(
        id="local.needs_wl",
        places_required=("workload:x",),
    )
    seat.assemble(dna)
    assert seat.admission().may_run_business is False
    assert any("place_failed:workload:x" in r for r in seat.admission().reasons)


def test_combined_os_and_workload_prefixes() -> None:
    eng = _engine_with_local()
    try:
        spawn = combined_structure_spawn_port(engine=eng)
        port = PlaceEffectPort(spawn=spawn)
        # workload works
        obs = port.apply(
            EffectIntent(kind=EffectIntentKind.ENSURE_PLACE, target="workload:a")
        )
        assert obs[0].kind.value == "place_ready"
        # os without body fails closed
        obs2 = port.apply(
            EffectIntent(kind=EffectIntentKind.ENSURE_PLACE, target="os:b")
        )
        assert obs2[0].kind.value == "place_failed"
    finally:
        eng.shutdown()
