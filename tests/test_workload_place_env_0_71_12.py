"""0.71.12 — invert workload_place spec env off isinstance(dict) soup.

Typed env at the Mapping payload boundary. Missing → empty. Non-mapping
fails closed (workload_spec_invalid). No silent drop to {}.
"""

from __future__ import annotations

from collections import UserDict
from collections.abc import Mapping
from pathlib import Path

from palm.core.workload import IsolationPolicy, WorkloadEngine, WorkloadStatus
from palm.core.workload.protocol import (
    RuntimeCapabilities,
    RuntimePollOutcome,
    RuntimeStartOutcome,
    RuntimeStopOutcome,
    WorkloadRuntime,
)
from palm.core.workload.spec import WorkloadSpec
from palm.system.structure.workload_place import WorkloadPlaceSpawn

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
        self.specs: list[WorkloadSpec] = []

    def capabilities(self) -> RuntimeCapabilities:
        return RuntimeCapabilities(
            name=self.name,
            isolation_modes=frozenset({IsolationPolicy.BEST_EFFORT}),
            kinds=frozenset({"run", "service", "workspace"}),
        )

    def start(self, workload_id, spec, *, owner=None):
        self.specs.append(spec)
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


def test_workload_place_source_has_no_env_dict_isinstance() -> None:
    text = _WORKLOAD_PLACE.read_text(encoding="utf-8")
    assert 'isinstance(body.get("env"), dict)' not in text
    assert "isinstance(body.get('env'), dict)" not in text


def test_ensure_accepts_dict_env_on_spec() -> None:
    spy = _SpyRuntime()
    eng = _engine(runtime=spy)
    try:
        hands = WorkloadPlaceSpawn(engine=eng)
        ready = hands.ensure("workload:barn", {"env": {"FARM": "1", "ROLE": "yard"}})
        assert ready.state == "ready"
        assert ready.reason == "workload_started"
        assert len(spy.specs) == 1
        assert spy.specs[0].env == {"FARM": "1", "ROLE": "yard"}
    finally:
        eng.shutdown()


def test_ensure_accepts_mapping_env_not_only_dict() -> None:
    spy = _SpyRuntime()
    eng = _engine(runtime=spy)
    try:
        hands = WorkloadPlaceSpawn(engine=eng)
        env: Mapping[str, str] = UserDict({"FARM": "2"})
        ready = hands.ensure("workload:paddock", {"env": env})
        assert ready.state == "ready"
        assert spy.specs[0].env == {"FARM": "2"}
    finally:
        eng.shutdown()


def test_ensure_missing_env_is_empty() -> None:
    spy = _SpyRuntime()
    eng = _engine(runtime=spy)
    try:
        hands = WorkloadPlaceSpawn(engine=eng)
        ready = hands.ensure("workload:field")
        assert ready.state == "ready"
        assert spy.specs[0].env == {}
    finally:
        eng.shutdown()


def test_ensure_non_mapping_env_fails_closed() -> None:
    spy = _SpyRuntime()
    eng = _engine(runtime=spy)
    try:
        hands = WorkloadPlaceSpawn(engine=eng)
        result = hands.ensure("workload:ghost", {"env": "FARM=1"})
        assert result.state == "failed"
        assert result.reason == "workload_spec_invalid"
        assert spy.specs == []
    finally:
        eng.shutdown()
