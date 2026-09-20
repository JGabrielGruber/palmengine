"""0.71.9 — compost place-registry overlay.

Bare / os: must not keep a second map beside the workload book.
Unbound: one local register. Bound: places is book projection only.
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
from palm.system.structure import PlaceEffectPort, combined_structure_spawn_port
from palm.system.structure.place_registry import InProcessPlaceRegistry
from palm.system.structure.place_spawn import os_prefix_spawn_port
from palm.system.structure.workload_place import adopt_prefix_spawn_port


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


def test_registry_has_no_overlay_field() -> None:
    names = {f.name for f in fields(InProcessPlaceRegistry)}
    assert "overlay" not in names


def test_unbound_bare_ensure_uses_local_register_only() -> None:
    port = PlaceEffectPort()
    obs = port.apply(
        EffectIntent(kind=EffectIntentKind.ENSURE_PLACE, target="support_home")
    )
    assert obs[0].kind.value == "place_ready"
    assert port.registry.places.get("support_home") == "ready"
    assert port.registry.book is None


def test_unbound_bare_release_clears_local_register() -> None:
    port = PlaceEffectPort()
    port.apply(EffectIntent(kind=EffectIntentKind.ENSURE_PLACE, target="support_home"))
    obs = port.apply(
        EffectIntent(kind=EffectIntentKind.RELEASE_PLACE, target="support_home")
    )
    assert obs[0].kind.value == "place_gone"
    assert "support_home" not in port.registry.places


def test_bound_bare_ensure_does_not_seed_second_map() -> None:
    eng = _engine()
    try:
        port = PlaceEffectPort(spawn=combined_structure_spawn_port(engine=eng))
        assert port.registry.book is eng
        obs = port.apply(
            EffectIntent(kind=EffectIntentKind.ENSURE_PLACE, target="support_home")
        )
        assert obs[0].kind.value == "place_ready"
        assert "support_home" not in port.registry.places
        assert "support_home" not in {wl.workload_id for wl in eng.list()}
    finally:
        eng.shutdown()


def test_bound_places_is_book_projection_only() -> None:
    eng = _engine()
    try:
        eng.adopt(
            "adopt:yard",
            WorkloadHandle(workload_id="adopt:yard", base_url="http://127.0.0.1:9"),
        )
        port = PlaceEffectPort(spawn=adopt_prefix_spawn_port(engine=eng))
        port.apply(
            EffectIntent(kind=EffectIntentKind.ENSURE_PLACE, target="support_home")
        )
        assert port.registry.places.get("adopt:yard") == "ready"
        assert "support_home" not in port.registry.places
    finally:
        eng.shutdown()


def test_os_failed_is_observation_not_registry_row() -> None:
    port = PlaceEffectPort(spawn=os_prefix_spawn_port())
    obs = port.apply(
        EffectIntent(kind=EffectIntentKind.ENSURE_PLACE, target="os:worker-a")
    )
    assert obs[0].kind.value == "place_failed"
    assert obs[0].payload.get("reason") == "os_spawn_not_configured"
    assert "os:worker-a" not in port.registry.places


def test_os_ready_unbound_lives_in_local_register() -> None:
    port = PlaceEffectPort(spawn=os_prefix_spawn_port())
    obs = port.apply(
        EffectIntent(
            kind=EffectIntentKind.ENSURE_PLACE,
            target="os:worker-a",
            payload={"handle": "pid-9"},
        )
    )
    assert obs[0].kind.value == "place_ready"
    assert port.registry.places.get("os:worker-a") == "ready"


def test_os_ready_bound_does_not_seed_second_map() -> None:
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
        assert obs[0].kind.value == "place_ready"
        assert "os:worker-a" not in port.registry.places
        assert "os:worker-a" not in {wl.workload_id for wl in eng.list()}
    finally:
        eng.shutdown()
