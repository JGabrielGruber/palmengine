"""0.71.13 — invert WorkloadEngine initialize runtime bind off isinstance soup.

Typed bind of named runtimes at the Mapping boundary. Missing → empty.
Non-mapping fails closed. Non-WorkloadRuntime values fail closed.
No isinstance(bound, dict) / isinstance(runtime, WorkloadRuntime) soup.
"""

from __future__ import annotations

from collections import UserDict
from collections.abc import Mapping
from pathlib import Path

import pytest

from palm.core.workload import IsolationPolicy, WorkloadEngine, WorkloadStatus
from palm.core.workload.protocol import (
    RuntimeCapabilities,
    RuntimePollOutcome,
    RuntimeStartOutcome,
    RuntimeStopOutcome,
    WorkloadRuntime,
)
from palm.core.workload.spec import (
    LifecyclePolicy,
    WorkloadKind,
    WorkloadPlacement,
    WorkloadSpec,
)
from tests.core.fakes.workload_runtime import FakeWorkloadRuntime

_ENGINE = (
    Path(__file__).resolve().parents[1]
    / "src"
    / "palm"
    / "core"
    / "workload"
    / "engine.py"
)


class _SpyRuntime(WorkloadRuntime):
    def __init__(self, *, name: str = "local") -> None:
        super().__init__(name=name)
        self.starts: list[str] = []

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
        return RuntimeStopOutcome(status=WorkloadStatus.STOPPED)


def test_engine_source_has_no_runtime_bind_isinstance_soup() -> None:
    text = _ENGINE.read_text(encoding="utf-8")
    assert "isinstance(bound, dict)" not in text
    assert "isinstance(runtime, WorkloadRuntime)" not in text


def test_initialize_binds_dict_of_named_runtimes() -> None:
    spy = _SpyRuntime(name="local")
    eng = WorkloadEngine()
    try:
        eng.initialize(runtimes={spy.name: spy}, default_runtime=spy.name)
        assert eng._runtimes["local"] is spy
        wl = eng.start(
            WorkloadSpec(
                kind=WorkloadKind.WORKSPACE,
                isolation=IsolationPolicy.BEST_EFFORT,
                lifecycle=LifecyclePolicy.SESSION,
                placement=WorkloadPlacement(runtime="local"),
            )
        )
        assert wl.status is WorkloadStatus.READY
        assert spy.starts == [wl.workload_id]
    finally:
        eng.shutdown()


def test_initialize_binds_mapping_not_only_dict() -> None:
    spy = _SpyRuntime(name="yard")
    named: Mapping[str, WorkloadRuntime] = UserDict({spy.name: spy})
    eng = WorkloadEngine()
    try:
        eng.initialize(runtimes=named, default_runtime=spy.name)
        assert eng._runtimes["yard"] is spy
    finally:
        eng.shutdown()


def test_initialize_missing_runtimes_is_empty() -> None:
    eng = WorkloadEngine()
    try:
        eng.initialize()
        assert eng._runtimes == {}
    finally:
        eng.shutdown()


def test_initialize_non_mapping_runtimes_fails_closed() -> None:
    eng = WorkloadEngine()
    with pytest.raises(TypeError, match="mapping"):
        eng.initialize(runtimes=["local"])  # type: ignore[arg-type]
    assert eng.is_initialized is False


def test_initialize_non_runtime_value_fails_closed() -> None:
    eng = WorkloadEngine()
    with pytest.raises(TypeError, match="WorkloadRuntime"):
        eng.initialize(runtimes={"local": object()})  # type: ignore[dict-item]
    assert eng.is_initialized is False


def test_initialize_still_accepts_fake_runtime() -> None:
    rt = FakeWorkloadRuntime()
    eng = WorkloadEngine()
    try:
        eng.initialize(runtimes={rt.name: rt}, default_runtime=rt.name)
        assert eng._runtimes[rt.name] is rt
    finally:
        eng.shutdown()
