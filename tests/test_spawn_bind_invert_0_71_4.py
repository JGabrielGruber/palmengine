"""0.71.4 — invert spawn-hand discovery off the handles duck-walk.

Typed book binds live on RegisteredPlaceSpawn. host_bind / place_registry
walk that table; they do not getattr(spawn, \"handles\") for bind hands.
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
    StructureSeat,
    WorkloadPlaceSpawn,
    adopt_prefix_spawn_port,
    bind_host_structure_to_seat,
    combined_structure_spawn_port,
    place_effect_port,
    workload_prefix_spawn_port,
    workload_spawn_hands,
)
from palm.system.structure.place_registry import engine_from_spawn
from palm.system.structure.place_spawn import RegisteredPlaceSpawn
from palm.system.structure.workload_place import AdoptPlaceSpawn

_STRUCTURE = Path(__file__).resolve().parents[1] / "src" / "palm" / "system" / "structure"


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


def test_prefix_ports_register_typed_binds_not_magic_handle_keys() -> None:
    eng = _engine()
    try:
        wl = workload_prefix_spawn_port(engine=eng)
        ad = adopt_prefix_spawn_port(engine=eng)
        assert isinstance(wl, RegisteredPlaceSpawn)
        assert isinstance(ad, RegisteredPlaceSpawn)
        assert not hasattr(wl, "handles")
        assert not hasattr(ad, "handles")
        assert len(wl.book_binds()) == 1
        assert len(ad.book_binds()) == 1
        assert isinstance(wl.book_binds()[0], WorkloadPlaceSpawn)
        assert isinstance(ad.book_binds()[0], AdoptPlaceSpawn)
        assert wl.book_engine() is eng
        assert ad.book_engine() is eng
    finally:
        eng.shutdown()


def test_combined_port_merges_binds_without_magic_keys() -> None:
    eng = _engine(runtime=_SpyRuntime())
    try:
        port = combined_structure_spawn_port(engine=eng)
        assert not hasattr(port, "handles")
        kinds = {type(h) for h in port.book_binds()}
        assert WorkloadPlaceSpawn in kinds
        assert AdoptPlaceSpawn in kinds
        assert port.book_engine() is eng
    finally:
        eng.shutdown()


def test_engine_from_spawn_uses_typed_binds() -> None:
    eng = _engine()
    try:
        spawn = adopt_prefix_spawn_port(engine=eng)
        assert engine_from_spawn(spawn) is eng
        bare = RegisteredPlaceSpawn()
        assert engine_from_spawn(bare) is None
        assert engine_from_spawn(object()) is None
    finally:
        eng.shutdown()


def test_place_effect_port_projects_via_typed_bind() -> None:
    eng = _engine()
    try:
        eng.adopt(
            "adopt:yard",
            WorkloadHandle(workload_id="adopt:yard", base_url="http://127.0.0.1:9"),
        )
        port = PlaceEffectPort(spawn=adopt_prefix_spawn_port(engine=eng))
        assert port.registry.book is eng
        assert port.registry.places.get("adopt:yard") == "ready"
    finally:
        eng.shutdown()


def test_bind_book_reattaches_engine_on_existing_binds() -> None:
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
        spawn = place_effect_port(seat.effects).spawn  # type: ignore[union-attr]
        assert engine_from_spawn(spawn) is eng
        hands = workload_spawn_hands(spawn)
        assert isinstance(hands, WorkloadPlaceSpawn)
        assert hands.engine is eng
        adopt = next(h for h in spawn.book_binds() if isinstance(h, AdoptPlaceSpawn))
        assert adopt.engine is eng
    finally:
        eng.shutdown()


def test_host_bind_and_registry_do_not_duck_walk_handles() -> None:
    """Consumers must not getattr(spawn, \"handles\") for book bind discovery."""
    forbidden = 'getattr(spawn, "handles"'
    for name in ("host_bind.py", "place_registry.py"):
        text = (_STRUCTURE / name).read_text(encoding="utf-8")
        assert forbidden not in text, f"{name} still duck-walks spawn.handles"
        assert "__workload_spawn__" not in text, f"{name} still names magic handle key"
        assert "__adopt_spawn__" not in text, f"{name} still names magic handle key"
