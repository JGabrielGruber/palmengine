"""0.71.6 — invert host_bind off getattr/isinstance duck nests.

host_bind takes a typed workload-bearing shell, StructureEffectPort /
PlaceEffectPort, and RegisteredPlaceSpawn workload_bind. It does not
getattr shell.workload / is_initialized, getattr effects.places, or
isinstance Protocol/hands nests for bind discovery.
"""

from __future__ import annotations

import re
from pathlib import Path

from palm.core.workload import IsolationPolicy, WorkloadEngine, WorkloadStatus
from palm.core.workload.protocol import (
    RuntimeCapabilities,
    RuntimePollOutcome,
    RuntimeStartOutcome,
    RuntimeStopOutcome,
    WorkloadRuntime,
)
from palm.system.structure import (
    PlaceEffectPort,
    RecordingEffectPort,
    StructureEffectPort,
    StructureSeat,
    WorkloadPlaceSpawn,
    bind_host_structure_to_seat,
    book_bind_port,
    combined_structure_spawn_port,
    default_structure_effects,
    place_effect_port,
    resolve_workload_engine,
    workload_spawn_hands,
)
from palm.system.structure.place_spawn import RegisteredPlaceSpawn
from palm.system.structure.workload_place import AdoptPlaceSpawn

_HOST_BIND = (
    Path(__file__).resolve().parents[1]
    / "src"
    / "palm"
    / "system"
    / "structure"
    / "host_bind.py"
)

_FORBIDDEN_GETATTR = re.compile(
    r'getattr\(\s*(?:shell|engine|effects)\s*,\s*"'
    r'(?:workload|is_initialized|places)"'
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


def test_host_bind_source_has_no_getattr_duck_nest() -> None:
    text = _HOST_BIND.read_text(encoding="utf-8")
    assert _FORBIDDEN_GETATTR.search(text) is None, text
    assert 'getattr(shell, "workload"' not in text
    assert 'getattr(engine, "is_initialized"' not in text
    assert 'getattr(effects, "places"' not in text


def test_host_bind_source_has_no_isinstance_protocol_nest() -> None:
    text = _HOST_BIND.read_text(encoding="utf-8")
    assert "isinstance(effects, PlaceEffectPort)" not in text
    assert "isinstance(spawn, BookBindPort)" not in text
    assert "isinstance(hands, WorkloadPlaceSpawn)" not in text
    assert "isinstance(places, PlaceEffectPort)" not in text


def test_resolve_workload_engine_typed_shell() -> None:
    class _Shell:
        workload: WorkloadEngine | None = None

    assert resolve_workload_engine(_Shell()) is None

    cold = WorkloadEngine()
    class _Cold:
        workload = cold

    assert resolve_workload_engine(_Cold()) is None

    eng = _engine()
    try:

        class _Ready:
            workload = eng

        assert resolve_workload_engine(_Ready()) is eng
    finally:
        eng.shutdown()


def test_place_effect_port_typed_carriers() -> None:
    bare = PlaceEffectPort()
    assert place_effect_port(bare) is bare
    structure = StructureEffectPort()
    assert place_effect_port(structure) is structure.places
    assert place_effect_port(RecordingEffectPort()) is None


def test_registered_spawn_exposes_typed_workload_bind() -> None:
    eng = _engine()
    try:
        port = combined_structure_spawn_port(engine=eng)
        assert isinstance(port, RegisteredPlaceSpawn)
        assert isinstance(port.workload_bind, WorkloadPlaceSpawn)
        assert port.workload_bind.engine is eng
        assert book_bind_port(port) is port
        assert workload_spawn_hands(port) is port.workload_bind
        assert workload_spawn_hands(port.fallback) is None
    finally:
        eng.shutdown()


def test_bind_host_structure_uses_typed_paths() -> None:
    eng = _engine(runtime=_SpyRuntime())
    try:

        class _Shell:
            workload = eng

        seat = StructureSeat(
            effects=PlaceEffectPort(spawn=combined_structure_spawn_port(engine=None))
        )
        report = bind_host_structure_to_seat(seat, _Shell(), bind_workload=True)
        assert report["bound"] is True
        assert report["engine"] is True
        assert report["spawn"] in {"existing", "already"}
        port = place_effect_port(seat.effects)
        assert port is not None
        hands = workload_spawn_hands(port.spawn)
        assert isinstance(hands, WorkloadPlaceSpawn)
        assert hands.engine is eng
        spawn = book_bind_port(port.spawn)
        assert spawn is not None
        adopt = next(h for h in spawn.book_binds() if isinstance(h, AdoptPlaceSpawn))
        assert adopt.engine is eng
    finally:
        eng.shutdown()


def test_default_structure_effects_engine_typed() -> None:
    eng = _engine()
    try:
        hands = default_structure_effects(engine=eng)
        assert isinstance(hands, StructureEffectPort)
        assert workload_spawn_hands(hands.spawn).engine is eng  # type: ignore[union-attr]
    finally:
        eng.shutdown()
