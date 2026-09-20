"""0.71.7 — invert place_registry engine_from_spawn off Protocol isinstance.

engine_from_spawn takes typed RegisteredPlaceSpawn book binds (same invert
as host_bind.book_bind_port). It does not isinstance(spawn, BookBindPort).
Adopt payload handle invert is `0.71.8` (typed WorkloadHandle only).
"""

from __future__ import annotations

from pathlib import Path

from palm.core.workload import IsolationPolicy, WorkloadEngine, WorkloadHandle, WorkloadStatus
from palm.core.workload.protocol import (
    RuntimeCapabilities,
    RuntimePollOutcome,
    RuntimeStartOutcome,
    RuntimeStopOutcome,
    WorkloadRuntime,
)
from palm.system.structure import (
    PlaceEffectPort,
    adopt_prefix_spawn_port,
    combined_structure_spawn_port,
)
from palm.system.structure.place_registry import engine_from_spawn
from palm.system.structure.place_spawn import InProcessPlaceSpawn, RegisteredPlaceSpawn

_PLACE_REGISTRY = (
    Path(__file__).resolve().parents[1]
    / "src"
    / "palm"
    / "system"
    / "structure"
    / "place_registry.py"
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


def test_place_registry_source_has_no_isinstance_book_bind_port() -> None:
    text = _PLACE_REGISTRY.read_text(encoding="utf-8")
    assert "isinstance(spawn, BookBindPort)" not in text
    assert "BookBindPort" not in text


def test_engine_from_spawn_typed_registered_place_spawn() -> None:
    eng = _engine()
    try:
        spawn = adopt_prefix_spawn_port(engine=eng)
        assert isinstance(spawn, RegisteredPlaceSpawn)
        assert engine_from_spawn(spawn) is eng
        assert engine_from_spawn(RegisteredPlaceSpawn()) is None
        assert engine_from_spawn(InProcessPlaceSpawn()) is None
        assert engine_from_spawn(object()) is None
    finally:
        eng.shutdown()


def test_place_effect_port_binds_book_via_typed_spawn() -> None:
    eng = _engine(runtime=_SpyRuntime())
    try:
        eng.adopt(
            "adopt:yard",
            WorkloadHandle(workload_id="adopt:yard", base_url="http://127.0.0.1:9"),
        )
        port = PlaceEffectPort(spawn=combined_structure_spawn_port(engine=eng))
        assert port.registry.book is eng
        assert port.registry.places.get("adopt:yard") == "ready"
        assert engine_from_spawn(port.spawn) is eng
    finally:
        eng.shutdown()
