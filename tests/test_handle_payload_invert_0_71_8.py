"""0.71.8 — invert adopt payload handle off dict | base_url dual.

AdoptPlaceSpawn / place→engine boundary takes typed WorkloadHandle only.
EffectIntent payload may still be a Mapping; dict handle and bare base_url
are not coerced at this boundary.
"""

from __future__ import annotations

from pathlib import Path

from palm.core.structure import EffectIntent, EffectIntentKind
from palm.core.workload import IsolationPolicy, WorkloadEngine, WorkloadHandle, WorkloadStatus
from palm.core.workload.protocol import (
    RuntimeCapabilities,
    RuntimePollOutcome,
    RuntimeStartOutcome,
    RuntimeStopOutcome,
    WorkloadRuntime,
)
from palm.system.structure import PlaceEffectPort, adopt_prefix_spawn_port
from palm.system.structure.workload_place import AdoptPlaceSpawn

_WORKLOAD_PLACE = (
    Path(__file__).resolve().parents[1]
    / "src"
    / "palm"
    / "system"
    / "structure"
    / "workload_place.py"
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


def test_workload_place_source_has_no_dict_or_base_url_handle_coercion() -> None:
    text = _WORKLOAD_PLACE.read_text(encoding="utf-8")
    assert "WorkloadHandle.from_dict" not in text
    assert 'body.get("base_url")' not in text
    assert "isinstance(raw, dict)" not in text


def test_ensure_accepts_typed_workload_handle_only() -> None:
    eng = _engine()
    try:
        hands = AdoptPlaceSpawn(engine=eng)
        handle = WorkloadHandle(workload_id="adopt:barn", base_url="http://127.0.0.1:8")
        ready = hands.ensure("adopt:barn", {"handle": handle})
        assert ready.state == "ready"
        assert ready.reason == "workload_adopted"
        row = eng.get("adopt:barn")
        assert row.handle is not None
        assert row.handle.base_url == "http://127.0.0.1:8"
    finally:
        eng.shutdown()


def test_ensure_dict_handle_fails_closed_not_coerced() -> None:
    eng = _engine()
    try:
        hands = AdoptPlaceSpawn(engine=eng)
        result = hands.ensure(
            "adopt:ghost",
            {"handle": {"workload_id": "adopt:ghost", "base_url": "http://127.0.0.1:9"}},
        )
        assert result.state == "failed"
        assert result.reason == "adopt_handle_missing"
    finally:
        eng.shutdown()


def test_ensure_bare_base_url_fails_closed_not_coerced() -> None:
    eng = _engine()
    try:
        hands = AdoptPlaceSpawn(engine=eng)
        result = hands.ensure("adopt:ghost", {"base_url": "http://127.0.0.1:9"})
        assert result.state == "failed"
        assert result.reason == "adopt_handle_missing"
    finally:
        eng.shutdown()


def test_place_effect_port_typed_handle_still_adopts() -> None:
    eng = _engine()
    try:
        port = PlaceEffectPort(spawn=adopt_prefix_spawn_port(engine=eng))
        handle = WorkloadHandle(workload_id="adopt:yard", base_url="http://127.0.0.1:9")
        obs = port.apply(
            EffectIntent(
                kind=EffectIntentKind.ENSURE_PLACE,
                target="adopt:yard",
                payload={"handle": handle},
            )
        )
        assert obs[0].kind.value == "place_ready"
        assert port.registry.places.get("adopt:yard") == "ready"
    finally:
        eng.shutdown()


def test_booked_adopt_still_converges_without_payload_handle() -> None:
    eng = _engine()
    try:
        eng.adopt(
            "adopt:yard",
            WorkloadHandle(workload_id="adopt:yard", base_url="http://127.0.0.1:9"),
        )
        port = PlaceEffectPort(spawn=adopt_prefix_spawn_port(engine=eng))
        obs = port.apply(EffectIntent(kind=EffectIntentKind.ENSURE_PLACE, target="adopt:yard"))
        assert obs[0].kind.value == "place_ready"
        assert obs[0].payload.get("spawn") == "workload_already"
    finally:
        eng.shutdown()
