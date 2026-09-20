"""0.71.3 — compost extra place maps.

Workload book is the body book. Spawn hands do not keep place_id → workload_id.
Overlay is not written for adopt / workload outcomes.
"""

from __future__ import annotations

from dataclasses import fields

from palm.core.structure import EffectIntent, EffectIntentKind
from palm.core.workload import IsolationPolicy, WorkloadEngine, WorkloadHandle, WorkloadStatus
from palm.core.workload.protocol import (
    RuntimeCapabilities,
    RuntimePollOutcome,
    RuntimeStartOutcome,
    RuntimeStopOutcome,
    WorkloadRuntime,
)
from palm.system.structure import PlaceEffectPort
from palm.system.structure.workload_place import (
    AdoptPlaceSpawn,
    WorkloadPlaceSpawn,
    adopt_prefix_spawn_port,
    workload_prefix_spawn_port,
)


class _SpyRuntime(WorkloadRuntime):
    def __init__(self, *, name: str = "local") -> None:
        super().__init__(name=name)

    def capabilities(self) -> RuntimeCapabilities:
        return RuntimeCapabilities(
            name=self.name,
            isolation_modes=frozenset({IsolationPolicy.BEST_EFFORT}),
            kinds=frozenset({"run", "service", "workspace"}),
        )

    def start(self, workload_id, spec, *, owner=None):
        return RuntimeStartOutcome(status=WorkloadStatus.READY)

    def poll(self, workload_id):
        return RuntimePollOutcome(status=WorkloadStatus.READY)

    def stop(self, workload_id):
        return RuntimeStopOutcome(status=WorkloadStatus.STOPPED)


def _engine(*, runtime: WorkloadRuntime | None = None) -> WorkloadEngine:
    eng = WorkloadEngine()
    if runtime is None:
        eng.initialize()
    else:
        eng.initialize(runtimes={runtime.name: runtime}, default_runtime=runtime.name)
    return eng


def test_spawn_hands_have_no_place_id_map() -> None:
    names = {f.name for f in fields(AdoptPlaceSpawn)}
    assert "places" not in names
    names = {f.name for f in fields(WorkloadPlaceSpawn)}
    assert "places" not in names


def test_ensure_adopt_does_not_write_overlay() -> None:
    eng = _engine()
    try:
        eng.adopt(
            "adopt:yard",
            WorkloadHandle(workload_id="adopt:yard", base_url="http://127.0.0.1:9"),
        )
        port = PlaceEffectPort(spawn=adopt_prefix_spawn_port(engine=eng))
        port.apply(EffectIntent(kind=EffectIntentKind.ENSURE_PLACE, target="adopt:yard"))
        assert "adopt:yard" not in port.registry.overlay
        assert port.registry.places.get("adopt:yard") == "ready"
    finally:
        eng.shutdown()


def test_failed_adopt_is_observation_not_overlay_row() -> None:
    eng = _engine()
    try:
        port = PlaceEffectPort(spawn=adopt_prefix_spawn_port(engine=eng))
        obs = port.apply(
            EffectIntent(kind=EffectIntentKind.ENSURE_PLACE, target="adopt:ghost")
        )
        assert obs[0].kind.value == "place_failed"
        assert "adopt:ghost" not in port.registry.overlay
        assert "adopt:ghost" not in port.registry.places
        assert "adopt:ghost" not in {wl.workload_id for wl in eng.list()}
    finally:
        eng.shutdown()


def test_workload_place_id_is_the_book_id() -> None:
    eng = _engine(runtime=_SpyRuntime())
    try:
        spawn = workload_prefix_spawn_port(engine=eng)
        port = PlaceEffectPort(spawn=spawn)
        obs = port.apply(
            EffectIntent(kind=EffectIntentKind.ENSURE_PLACE, target="workload:manor")
        )
        assert obs[0].kind.value == "place_ready"
        booked = eng.get("workload:manor")
        assert booked.status is WorkloadStatus.READY
        assert "workload:manor" not in port.registry.overlay
        assert port.registry.places.get("workload:manor") == "ready"
        eng.stop("workload:manor")
        assert "workload:manor" not in port.registry.places
    finally:
        eng.shutdown()


def test_reensure_adopt_reads_book_not_a_hand_map() -> None:
    eng = _engine()
    try:
        eng.adopt(
            "adopt:yard",
            WorkloadHandle(workload_id="adopt:yard", base_url="http://127.0.0.1:9"),
        )
        hands = AdoptPlaceSpawn(engine=eng)
        first = hands.ensure("adopt:yard", {})
        second = hands.ensure("adopt:yard", {})
        assert first.state == "ready"
        assert second.state == "ready"
        assert second.reason == "workload_already"
    finally:
        eng.shutdown()


def test_bare_id_still_uses_overlay() -> None:
    port = PlaceEffectPort()
    port.apply(EffectIntent(kind=EffectIntentKind.ENSURE_PLACE, target="support_home"))
    assert port.registry.overlay.get("support_home") == "ready"
