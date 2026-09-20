"""0.71.1 — adopt a named existing body into the workload book.

No WorkloadRuntime.start. Missing handle fails closed. Structure ENSURE
and places_required converge when the book already holds the place.
"""

from __future__ import annotations

from palm.core.structure import (
    EffectIntent,
    EffectIntentKind,
    StructureDefinition,
    StructurePhase,
)
from palm.core.workload import (
    IsolationPolicy,
    WorkloadEngine,
    WorkloadHandle,
    WorkloadSpecError,
    WorkloadStatus,
)
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
    combined_structure_spawn_port,
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


def _engine() -> WorkloadEngine:
    eng = WorkloadEngine()
    eng.initialize()
    return eng


def test_adopt_records_ready_in_workload_book() -> None:
    eng = _engine()
    try:
        wl = eng.adopt("adopt:yard", _handle())
        assert wl.status is WorkloadStatus.READY
        assert wl.handle is not None
        assert wl.handle.base_url == "http://127.0.0.1:9"
        booked = eng.get("adopt:yard")
        assert booked.status is WorkloadStatus.READY
        assert booked.handle is not None
        assert booked.handle.base_url == "http://127.0.0.1:9"
        assert booked.runtime == ""
    finally:
        eng.shutdown()


def test_adopt_does_not_call_runtime_start() -> None:
    spy = _SpyRuntime()
    eng = WorkloadEngine()
    eng.initialize(runtimes={"local": spy}, default_runtime="local")
    try:
        eng.adopt("adopt:yard", _handle())
        assert spy.starts == []
    finally:
        eng.shutdown()
    assert spy.stops == []


def test_adopt_empty_id_fails_closed() -> None:
    import pytest

    eng = _engine()
    try:
        with pytest.raises(WorkloadSpecError):
            eng.adopt("", _handle())
        with pytest.raises(WorkloadSpecError):
            eng.adopt("   ", _handle())
    finally:
        eng.shutdown()


def test_adopt_missing_handle_fails_closed() -> None:
    import pytest

    eng = _engine()
    try:
        with pytest.raises(WorkloadSpecError):
            eng.adopt("adopt:yard", None)
        with pytest.raises(WorkloadSpecError):
            eng.adopt("adopt:yard", WorkloadHandle(workload_id="adopt:yard"))
    finally:
        eng.shutdown()


def test_ensure_adopt_place_converges_from_book() -> None:
    from palm.system.structure.workload_place import adopt_prefix_spawn_port

    eng = _engine()
    try:
        eng.adopt("adopt:yard", _handle())
        port = PlaceEffectPort(spawn=adopt_prefix_spawn_port(engine=eng))
        obs = port.apply(EffectIntent(kind=EffectIntentKind.ENSURE_PLACE, target="adopt:yard"))
        assert obs[0].kind.value == "place_ready"
        assert "adopt:yard" in port.registry.places
        assert port.registry.places["adopt:yard"] == "ready"
    finally:
        eng.shutdown()


def test_ensure_adopt_without_handle_fails_closed() -> None:
    from palm.system.structure.workload_place import adopt_prefix_spawn_port

    eng = _engine()
    try:
        port = PlaceEffectPort(spawn=adopt_prefix_spawn_port(engine=eng))
        obs = port.apply(EffectIntent(kind=EffectIntentKind.ENSURE_PLACE, target="adopt:ghost"))
        assert obs[0].kind.value == "place_failed"
        assert obs[0].payload.get("reason") == "adopt_handle_missing"
        assert "adopt:ghost" not in port.registry.places
    finally:
        eng.shutdown()


def test_seat_places_required_adopt_converges() -> None:
    from palm.system.structure.workload_place import adopt_prefix_spawn_port

    eng = _engine()
    try:
        eng.adopt(
            "adopt:manor",
            WorkloadHandle(workload_id="adopt:manor", base_url="http://127.0.0.1:11"),
        )
        seat = StructureSeat(effects=PlaceEffectPort(spawn=adopt_prefix_spawn_port(engine=eng)))
        dna = StructureDefinition(
            id="local.with_adopted_place",
            places_required=("adopt:manor",),
        )
        seat.assemble(dna)
        assert seat.admission().may_run_business is True
        assert seat.admission().phase is StructurePhase.READY
    finally:
        eng.shutdown()


def test_combined_port_adopt_prefix_fail_closed_and_ready() -> None:
    eng = _engine()
    try:
        spawn = combined_structure_spawn_port(engine=eng)
        port = PlaceEffectPort(spawn=spawn)
        missing = port.apply(EffectIntent(kind=EffectIntentKind.ENSURE_PLACE, target="adopt:x"))
        assert missing[0].kind.value == "place_failed"
        eng.adopt("adopt:x", WorkloadHandle(workload_id="adopt:x", base_url="http://127.0.0.1:8"))
        ready = port.apply(EffectIntent(kind=EffectIntentKind.ENSURE_PLACE, target="adopt:x"))
        assert ready[0].kind.value == "place_ready"
    finally:
        eng.shutdown()
