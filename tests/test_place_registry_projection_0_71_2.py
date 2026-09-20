"""0.71.2 — InProcessPlaceRegistry projects the workload book.

Adopted and workload: readiness is the book, not a copied dict.
Bare in-process ids stay a local overlay (named residual).
"""

from __future__ import annotations

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
from palm.system.structure.workload_place import (
    adopt_prefix_spawn_port,
    workload_prefix_spawn_port,
)


class _SpyRuntime(WorkloadRuntime):
    def __init__(self, *, name: str = "local") -> None:
        super().__init__(name=name)
        self.starts: list[str] = []
        self.stops: list[str] = []

    def capabilities(self) -> RuntimeCapabilities:
        return RuntimeCapabilities(
            name=self.name,
            isolation_modes=frozenset({IsolationPolicy.BEST_EFFORT}),
            kinds=frozenset({"run", "service", "workspace"}),
        )

    def start(self, workload_id, spec, *, owner=None):
        self.starts.append(workload_id)
        return RuntimeStartOutcome(status=WorkloadStatus.READY)

    def poll(self, workload_id):
        return RuntimePollOutcome(status=WorkloadStatus.READY)

    def stop(self, workload_id):
        self.stops.append(workload_id)
        return RuntimeStopOutcome(status=WorkloadStatus.STOPPED)


def _handle(
    workload_id: str = "adopt:yard",
    base_url: str = "http://127.0.0.1:9",
) -> WorkloadHandle:
    return WorkloadHandle(workload_id=workload_id, base_url=base_url)


def _engine(*, runtime: WorkloadRuntime | None = None) -> WorkloadEngine:
    eng = WorkloadEngine()
    if runtime is None:
        eng.initialize()
    else:
        eng.initialize(runtimes={runtime.name: runtime}, default_runtime=runtime.name)
    return eng


def test_adopt_projects_ready_from_book_without_ensure() -> None:
    eng = _engine()
    try:
        eng.adopt("adopt:yard", _handle())
        port = PlaceEffectPort(spawn=adopt_prefix_spawn_port(engine=eng))
        assert port.registry.places.get("adopt:yard") == "ready"
        assert eng.get("adopt:yard").status is WorkloadStatus.READY
    finally:
        eng.shutdown()


def test_adopt_unbind_drops_projection_without_release_intent() -> None:
    eng = _engine()
    try:
        eng.adopt("adopt:yard", _handle())
        port = PlaceEffectPort(spawn=adopt_prefix_spawn_port(engine=eng))
        port.apply(EffectIntent(kind=EffectIntentKind.ENSURE_PLACE, target="adopt:yard"))
        assert port.registry.places.get("adopt:yard") == "ready"
        eng.stop("adopt:yard")
        assert eng.get("adopt:yard").status is WorkloadStatus.STOPPED
        assert port.registry.places.get("adopt:yard") != "ready"
        assert "adopt:yard" not in port.registry.places
    finally:
        eng.shutdown()


def test_workload_prefix_projects_then_drops_on_engine_stop() -> None:
    spy = _SpyRuntime()
    eng = _engine(runtime=spy)
    try:
        spawn = workload_prefix_spawn_port(engine=eng)
        port = PlaceEffectPort(spawn=spawn)
        obs = port.apply(
            EffectIntent(kind=EffectIntentKind.ENSURE_PLACE, target="workload:manor")
        )
        assert obs[0].kind.value == "place_ready"
        assert port.registry.places.get("workload:manor") == "ready"
        eng.stop("workload:manor")
        assert port.registry.places.get("workload:manor") != "ready"
        assert "workload:manor" not in port.registry.places
    finally:
        eng.shutdown()


def test_failed_adopt_overlay_is_not_a_book_row() -> None:
    eng = _engine()
    try:
        port = PlaceEffectPort(spawn=adopt_prefix_spawn_port(engine=eng))
        obs = port.apply(
            EffectIntent(kind=EffectIntentKind.ENSURE_PLACE, target="adopt:ghost")
        )
        assert obs[0].kind.value == "place_failed"
        assert "adopt:ghost" not in port.registry.places
        ids = {wl.workload_id for wl in eng.list()}
        assert "adopt:ghost" not in ids
    finally:
        eng.shutdown()


def test_bare_in_process_id_stays_local_overlay() -> None:
    port = PlaceEffectPort()
    obs = port.apply(
        EffectIntent(kind=EffectIntentKind.ENSURE_PLACE, target="support_home")
    )
    assert obs[0].kind.value == "place_ready"
    assert port.registry.places.get("support_home") == "ready"


def test_combined_port_projects_adopt_from_book() -> None:
    eng = _engine()
    try:
        eng.adopt(
            "adopt:x",
            WorkloadHandle(workload_id="adopt:x", base_url="http://127.0.0.1:8"),
        )
        port = PlaceEffectPort(spawn=combined_structure_spawn_port(engine=eng))
        assert port.registry.places.get("adopt:x") == "ready"
    finally:
        eng.shutdown()
