"""0.71.5 — invert workload book row reads off getattr duck-typing.

place_registry / workload_place read Workload / WorkloadHandle fields typed.
They do not getattr status / workload_id / spec / labels / message / runtime
on book rows.
"""

from __future__ import annotations

import re
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
from palm.core.workload.record import Workload
from palm.core.workload.spec import (
    LifecyclePolicy,
    WorkloadKind,
    WorkloadPlacement,
    WorkloadSpec,
)
from palm.system.structure import PlaceEffectPort
from palm.system.structure.place_registry import (
    InProcessPlaceRegistry,
    _place_id_for,
    _project_state,
)
from palm.system.structure.workload_place import (
    AdoptPlaceSpawn,
    WorkloadPlaceSpawn,
    adopt_prefix_spawn_port,
    workload_prefix_spawn_port,
)

_STRUCTURE = Path(__file__).resolve().parents[1] / "src" / "palm" / "system" / "structure"

_ROW_ATTR_GETATTR = re.compile(
    r'getattr\(\s*(?:workload|wl|existing|row|spec)\s*,\s*"'
    r'(?:status|workload_id|spec|labels|message|runtime|result)"'
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


def _spec(*, place_id: str | None = None, workload_id: str = "w1") -> WorkloadSpec:
    labels = {"structure_place": place_id} if place_id else {}
    return WorkloadSpec(
        kind=WorkloadKind.WORKSPACE,
        isolation=IsolationPolicy.BEST_EFFORT,
        lifecycle=LifecyclePolicy.LEASE,
        labels=labels,
        placement=WorkloadPlacement(runtime="local"),
    )


def test_structure_files_do_not_getattr_book_row_fields() -> None:
    """Consumers must not getattr Workload row fields for book projection/spawn."""
    for name in ("place_registry.py", "workload_place.py"):
        text = (_STRUCTURE / name).read_text(encoding="utf-8")
        hits = _ROW_ATTR_GETATTR.findall(text)
        assert not hits, f"{name} still getattr-ducks book rows: {hits}"
        for needle in (
            'getattr(workload, "spec"',
            'getattr(workload, "workload_id"',
            'getattr(workload, "status"',
            'getattr(existing, "status"',
            'getattr(existing, "workload_id"',
            'getattr(wl, "status"',
            'getattr(wl, "workload_id"',
            'getattr(wl, "message"',
            'getattr(wl, "runtime"',
            'getattr(row, "workload_id"',
            'getattr(spec, "labels"',
        ):
            assert needle not in text, f"{name} still contains {needle}"


def test_place_id_and_project_state_read_typed_workload() -> None:
    wl = Workload(
        workload_id="book:id",
        spec=_spec(place_id="structure:label"),
        status=WorkloadStatus.READY,
        runtime="local",
    )
    assert _place_id_for(wl) == "structure:label"
    assert _project_state(wl) == "ready"

    bare = Workload(
        workload_id="bare-id",
        spec=_spec(),
        status=WorkloadStatus.READY,
        runtime="",
    )
    assert _place_id_for(bare) == "bare-id"
    assert _project_state(bare) == "ready"

    failed = Workload(
        workload_id="fail-id",
        spec=_spec(),
        status=WorkloadStatus.FAILED,
        runtime="local",
        message="boom",
    )
    assert _project_state(failed) == "failed"

    stopped = Workload(
        workload_id="stop-id",
        spec=_spec(),
        status=WorkloadStatus.STOPPED,
        runtime="local",
    )
    assert _project_state(stopped) is None


def test_registry_projects_typed_book_rows() -> None:
    eng = _engine()
    try:
        eng.adopt(
            "adopt:yard",
            WorkloadHandle(workload_id="adopt:yard", base_url="http://127.0.0.1:9"),
        )
        reg = InProcessPlaceRegistry()
        reg.bind_book(eng)
        assert reg.places.get("adopt:yard") == "ready"
        assert isinstance(eng.get("adopt:yard"), Workload)
    finally:
        eng.shutdown()


def test_workload_ensure_reads_typed_row_fields() -> None:
    spy = _SpyRuntime()
    eng = _engine(runtime=spy)
    try:
        hands = WorkloadPlaceSpawn(engine=eng)
        first = hands.ensure("workload:manor")
        assert first.state == "ready"
        assert first.reason == "workload_started"
        assert isinstance(first.handle, str)
        row = eng.get("workload:manor")
        assert isinstance(row, Workload)
        assert row.status is WorkloadStatus.READY
        again = hands.ensure("workload:manor")
        assert again.state == "ready"
        assert again.reason == "workload_already"
        assert again.payload["status"] == str(WorkloadStatus.READY)
        released = hands.release("workload:manor")
        assert released.state == "gone"
        assert eng.get("workload:manor").status is WorkloadStatus.STOPPED
    finally:
        eng.shutdown()


def test_adopt_ensure_reads_typed_row_and_handle() -> None:
    eng = _engine()
    try:
        hands = AdoptPlaceSpawn(engine=eng)
        handle = WorkloadHandle(workload_id="adopt:barn", base_url="http://127.0.0.1:8")
        first = hands.ensure("adopt:barn", {"handle": handle})
        assert first.state == "ready"
        assert first.reason == "workload_adopted"
        row = eng.get("adopt:barn")
        assert isinstance(row, Workload)
        assert row.handle is not None
        assert isinstance(row.handle, WorkloadHandle)
        assert row.handle.base_url == "http://127.0.0.1:8"
        again = hands.ensure("adopt:barn")
        assert again.state == "ready"
        assert again.reason == "workload_already"
    finally:
        eng.shutdown()


def test_place_effect_port_still_projects_after_typed_reads() -> None:
    eng = _engine(runtime=_SpyRuntime())
    try:
        port = PlaceEffectPort(spawn=workload_prefix_spawn_port(engine=eng))
        obs = port.apply(
            EffectIntent(kind=EffectIntentKind.ENSURE_PLACE, target="workload:manor")
        )
        assert obs[0].kind.value == "place_ready"
        assert port.registry.places.get("workload:manor") == "ready"
        adopt = PlaceEffectPort(spawn=adopt_prefix_spawn_port(engine=eng))
        eng.adopt(
            "adopt:yard",
            WorkloadHandle(workload_id="adopt:yard", base_url="http://127.0.0.1:9"),
        )
        adopt.bind_book_from_spawn()
        assert adopt.registry.places.get("adopt:yard") == "ready"
    finally:
        eng.shutdown()
