"""0.71.1 floor tests — place registry adopt into the workload book.

Invariants proven:
1. Adopt with WorkloadHandle.base_url -> record ready in workload book.
2. Structure ENSURE_PLACE / places_required converges; admission may run business.
3. Empty id or missing handle -> fail closed (not in-process success).
4. Adopt path must not call WorkloadRuntime.start.
5. Release of an adopted place unbinds (not SIGKILL).
"""

from __future__ import annotations

from typing import Any

import pytest

from palm.core.structure import (
    EffectIntent,
    EffectIntentKind,
    StructureDefinition,
    StructurePhase,
)
from palm.core.workload import (
    RuntimeCapabilities,
    RuntimeHealth,
    RuntimePollOutcome,
    RuntimeStartOutcome,
    RuntimeStopOutcome,
    WorkloadEngine,
    WorkloadHandle,
    WorkloadSpec,
    WorkloadSpecError,
    WorkloadStatus,
)
from palm.core.workload.protocol import WorkloadRuntime
from palm.runners.local.runtime import LocalWorkloadRuntime
from palm.system.structure import (
    PlaceEffectPort,
    StructureSeat,
    combined_structure_spawn_port,
)


class SpyForbiddenRuntime(WorkloadRuntime):
    """Runtime that fails if start() is invoked."""

    def __init__(self, name: str = "forbidden") -> None:
        super().__init__(name=name)
        self.start_called = False

    def capabilities(self) -> RuntimeCapabilities:
        from palm.core.workload import IsolationPolicy

        return RuntimeCapabilities(
            name=self.name,
            isolation_modes=frozenset({IsolationPolicy.BEST_EFFORT}),
            kinds=frozenset({"service"}),
            description="forbidden spy",
        )

    def health(self) -> RuntimeHealth:
        return RuntimeHealth(name=self.name, available=True, enabled=True)

    def start(self, workload_id: str, spec: WorkloadSpec, **kwargs: Any) -> RuntimeStartOutcome:
        self.start_called = True
        raise AssertionError("WorkloadRuntime.start must NOT be called on adopt path!")

    def exec(
        self,
        workload_id: str,
        command: list[str] | tuple[str, ...],
        *,
        timeout_s: float | None = None,
        env: dict[str, str] | None = None,
    ) -> Any:
        raise NotImplementedError

    def poll(self, workload_id: str) -> RuntimePollOutcome:
        return RuntimePollOutcome(status=WorkloadStatus.READY)

    def stop(self, workload_id: str) -> RuntimeStopOutcome:
        return RuntimeStopOutcome(status=WorkloadStatus.STOPPED)


def _engine_with_local() -> WorkloadEngine:
    eng = WorkloadEngine()
    eng.initialize(
        default_runtime="local",
        runtimes={"local": LocalWorkloadRuntime(name="local")},
    )
    return eng


def test_adopt_records_ready_in_workload_book() -> None:
    eng = _engine_with_local()
    try:
        wid = "place-svc-1"
        handle = WorkloadHandle(workload_id=wid, base_url="http://127.0.0.1:8080")
        wl = eng.adopt(wid, handle=handle)

        assert wl.workload_id == wid
        assert wl.status is WorkloadStatus.READY
        assert wl.runtime == "adopted"
        assert wl.handle is not None
        assert wl.handle.base_url == "http://127.0.0.1:8080"

        # Lookup by id
        fetched = eng.get(wid)
        assert fetched.status is WorkloadStatus.READY
        assert fetched.handle == handle

        # Appears in engine.list()
        listed = eng.list()
        assert any(item.workload_id == wid for item in listed)
    finally:
        eng.shutdown()


def test_adopt_fail_closed_empty_id() -> None:
    eng = _engine_with_local()
    try:
        handle = WorkloadHandle(workload_id="x", base_url="http://127.0.0.1:8080")
        with pytest.raises(WorkloadSpecError, match="empty"):
            eng.adopt("", handle=handle)
        with pytest.raises(WorkloadSpecError, match="empty"):
            eng.adopt("   ", handle=handle)
    finally:
        eng.shutdown()


def test_adopt_fail_closed_missing_handle() -> None:
    eng = _engine_with_local()
    try:
        # None handle
        with pytest.raises(WorkloadSpecError, match="handle"):
            eng.adopt("place-svc-2", handle=None)

        # Handle without base_url or connection hints
        empty_handle = WorkloadHandle(workload_id="place-svc-2")
        with pytest.raises(WorkloadSpecError, match="base_url"):
            eng.adopt("place-svc-2", handle=empty_handle)
    finally:
        eng.shutdown()


def test_adopt_does_not_call_runtime_start() -> None:
    spy = SpyForbiddenRuntime(name="spy")
    eng = WorkloadEngine()
    eng.initialize(
        default_runtime="spy",
        runtimes={"spy": spy},
    )
    try:
        handle = WorkloadHandle(workload_id="place-safe", base_url="http://127.0.0.1:9999")
        wl = eng.adopt("place-safe", handle=handle)
        assert wl.status is WorkloadStatus.READY
        assert spy.start_called is False
    finally:
        eng.shutdown()


def test_structure_ensure_converges_with_preadopted_place() -> None:
    eng = _engine_with_local()
    try:
        wid = "adopt:manor"
        eng.adopt(wid, handle=WorkloadHandle(workload_id=wid, base_url="http://127.0.0.1:9000"))

        seat = StructureSeat(
            effects=PlaceEffectPort(spawn=combined_structure_spawn_port(engine=eng))
        )
        dna = StructureDefinition(
            id="local.with_adopted_place",
            places_required=(wid,),
        )
        seat.assemble(dna)
        assert seat.admission().may_run_business is True
        assert seat.admission().phase is StructurePhase.READY
    finally:
        eng.shutdown()


def test_structure_ensure_converges_with_handle_payload() -> None:
    eng = _engine_with_local()
    try:
        spawn = combined_structure_spawn_port(engine=eng)
        port = PlaceEffectPort(spawn=spawn)
        obs = port.apply(
            EffectIntent(
                kind=EffectIntentKind.ENSURE_PLACE,
                target="adopt:yard",
                payload={"base_url": "http://127.0.0.1:9001"},
            )
        )
        assert obs[0].kind.value == "place_ready"
        assert obs[0].payload.get("spawn") == "workload_adopted"
        assert "adopt:yard" in port.registry.places

        # Workload book recorded ready
        wl = eng.get("adopt:yard")
        assert wl.status is WorkloadStatus.READY
        assert wl.handle is not None
        assert wl.handle.base_url == "http://127.0.0.1:9001"
    finally:
        eng.shutdown()


def test_structure_ensure_fails_closed_missing_handle() -> None:
    eng = _engine_with_local()
    try:
        seat = StructureSeat(
            effects=PlaceEffectPort(spawn=combined_structure_spawn_port(engine=eng))
        )
        dna = StructureDefinition(
            id="local.missing_handle",
            places_required=("adopt:unconfigured",),
        )
        seat.assemble(dna)
        assert seat.admission().may_run_business is False
        assert any("place_failed:adopt:unconfigured" in r for r in seat.admission().reasons)
    finally:
        eng.shutdown()


def test_structure_ensure_fails_closed_unbound_engine() -> None:
    spawn = combined_structure_spawn_port(engine=None)
    port = PlaceEffectPort(spawn=spawn)
    obs = port.apply(
        EffectIntent(
            kind=EffectIntentKind.ENSURE_PLACE,
            target="adopt:noeng",
            payload={"base_url": "http://127.0.0.1:9002"},
        )
    )
    assert obs[0].kind.value == "place_failed"
    assert obs[0].payload.get("reason") == "workload_engine_not_bound"


def test_structure_ensure_fails_closed_empty_id() -> None:
    eng = _engine_with_local()
    try:
        spawn = combined_structure_spawn_port(engine=eng)
        port = PlaceEffectPort(spawn=spawn)
        obs = port.apply(
            EffectIntent(
                kind=EffectIntentKind.ENSURE_PLACE,
                target="adopt:",
                payload={"base_url": "http://127.0.0.1:9002"},
            )
        )
        assert obs[0].kind.value == "place_failed"
        assert obs[0].payload.get("reason") == "empty_place_id"
    finally:
        eng.shutdown()


def test_structure_release_unbinds_without_sigkill() -> None:
    eng = _engine_with_local()
    try:
        spawn = combined_structure_spawn_port(engine=eng)
        port = PlaceEffectPort(spawn=spawn)

        # Ensure first
        port.apply(
            EffectIntent(
                kind=EffectIntentKind.ENSURE_PLACE,
                target="adopt:transient",
                payload={"base_url": "http://127.0.0.1:9003"},
            )
        )
        assert "adopt:transient" in port.registry.places

        # Release
        gone = port.apply(
            EffectIntent(
                kind=EffectIntentKind.RELEASE_PLACE,
                target="adopt:transient",
            )
        )
        assert gone[0].kind.value == "place_gone"
        assert gone[0].payload.get("spawn") == "adopt_unbound"
        assert "adopt:transient" not in port.registry.places
    finally:
        eng.shutdown()


def test_combined_spawn_port_routes_all_prefixes() -> None:
    eng = _engine_with_local()
    try:
        spawn = combined_structure_spawn_port(engine=eng)
        port = PlaceEffectPort(spawn=spawn)

        # 1. workload: prefix routes to WorkloadPlaceSpawn
        wl_obs = port.apply(
            EffectIntent(kind=EffectIntentKind.ENSURE_PLACE, target="workload:wl-a")
        )
        assert wl_obs[0].kind.value == "place_ready"
        assert wl_obs[0].payload.get("spawn") == "workload_started"

        # 2. os: prefix without body fails closed
        os_obs = port.apply(
            EffectIntent(kind=EffectIntentKind.ENSURE_PLACE, target="os:os-a")
        )
        assert os_obs[0].kind.value == "place_failed"

        # 3. adopt: prefix with handle succeeds
        adopt_obs = port.apply(
            EffectIntent(
                kind=EffectIntentKind.ENSURE_PLACE,
                target="adopt:ad-a",
                payload={"base_url": "http://127.0.0.1:9004"},
            )
        )
        assert adopt_obs[0].kind.value == "place_ready"
        assert adopt_obs[0].payload.get("spawn") == "workload_adopted"

        # 4. Bare place id falls through to in-process success
        bare_obs = port.apply(
            EffectIntent(kind=EffectIntentKind.ENSURE_PLACE, target="bare-a")
        )
        assert bare_obs[0].kind.value == "place_ready"
        assert bare_obs[0].payload.get("spawn") == "in_process"
    finally:
        eng.shutdown()
