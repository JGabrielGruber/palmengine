"""0.63.14 — place spawn port: OS hands contract, fail closed without body."""

from __future__ import annotations

from palm.core.structure import (
    EffectIntent,
    EffectIntentKind,
    StructureDefinition,
    StructurePhase,
)
from palm.system.structure import (
    PlaceEffectPort,
    PlaceSpawnResult,
    RegisteredPlaceSpawn,
    StructureSeat,
    os_prefix_spawn_port,
)


def test_in_process_default_unchanged() -> None:
    port = PlaceEffectPort()
    obs = port.apply(
        EffectIntent(kind=EffectIntentKind.ENSURE_PLACE, target="support_home")
    )
    assert obs[0].kind.value == "place_ready"
    assert port.registry.places["support_home"] == "ready"


def test_os_prefix_fail_closed_without_body() -> None:
    spawn = os_prefix_spawn_port()
    port = PlaceEffectPort(spawn=spawn)
    obs = port.apply(
        EffectIntent(kind=EffectIntentKind.ENSURE_PLACE, target="os:worker-a")
    )
    assert obs[0].kind.value == "place_failed"
    assert obs[0].payload.get("reason") == "os_spawn_not_configured"
    assert "os:worker-a" not in port.registry.places


def test_os_prefix_ready_when_body_provided() -> None:
    spawn = os_prefix_spawn_port()
    port = PlaceEffectPort(spawn=spawn)
    obs = port.apply(
        EffectIntent(
            kind=EffectIntentKind.ENSURE_PLACE,
            target="os:worker-a",
            payload={"handle": "pid-9"},
        )
    )
    assert obs[0].kind.value == "place_ready"
    assert port.registry.places["os:worker-a"] == "ready"


def test_registered_place_spawn_exact() -> None:
    calls: list[str] = []

    def ensure_yard(place_id: str, payload: dict) -> PlaceSpawnResult:
        calls.append(place_id)
        return PlaceSpawnResult(state="ready", reason="registered", handle="yard-1")

    spawn = RegisteredPlaceSpawn()
    spawn.register("work_yard", ensure=ensure_yard)
    port = PlaceEffectPort(spawn=spawn)
    obs = port.apply(EffectIntent(kind=EffectIntentKind.ENSURE_PLACE, target="work_yard"))
    assert calls == ["work_yard"]
    assert obs[0].kind.value == "place_ready"


def test_seat_assemble_os_place_blocks_admission() -> None:
    seat = StructureSeat(effects=PlaceEffectPort(spawn=os_prefix_spawn_port()))
    dna = StructureDefinition(
        id="local.needs_os",
        version="1",
        places_required=("os:edge",),
    )
    seat.assemble(dna)
    assert seat.admission().may_run_business is False
    assert seat.admission().phase is StructurePhase.BLOCKED
    assert any("place_failed:os:edge" in r for r in seat.admission().reasons)
