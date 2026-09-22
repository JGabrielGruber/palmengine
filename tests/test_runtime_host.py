"""Tests for RuntimeHost protocol decoupling."""

from __future__ import annotations

import pytest

from palm.common import DefinitionExecutor
from palm.system.runtime.host import RuntimeHost
from palm.system.runtime.schedulers import InlineScheduler
from palm.core.event import EventEngine
from palm.core.orchestration import OrchestrationEngine
from palm.definitions.flow import FlowDefinition
from bundles.standard.runtimes.daemon import DaemonRuntime
from bundles.standard.runtimes.embedded import EmbeddedRuntime
from tests.core.fakes.runner import TestRunner


class _MinimalHost:
    """Lightweight runtime double for executions-layer tests."""

    def __init__(self) -> None:
        self.orchestration = OrchestrationEngine()
        self.event = EventEngine()
        self.resource = None
        self._started = False
        self._execution = self  # thin double: port methods on self where needed

    @property
    def is_started(self) -> bool:
        return self._started

    @property
    def execution(self) -> object:
        return self._execution

    @property
    def admission(self) -> object:
        """0.63.4 — doubles publish admission; no silent bypass of the gate."""
        from palm.core.structure import AdmissionSnapshot, StructurePhase

        if self._started:
            return AdmissionSnapshot(
                may_run_business=True,
                phase=StructurePhase.READY,
                definition_id="test.minimal",
                definition_version="1",
            )
        return AdmissionSnapshot.empty()

    def resume_job(self, job_id: str) -> object:
        return self.orchestration.resume_job(job_id)

    def list_jobs(self, status: object = None) -> list:
        return self.orchestration.list_jobs(status=status)

    def start(self) -> None:
        self.event.initialize()
        self.orchestration.initialize(scheduler=InlineScheduler(runner=TestRunner()))
        self.orchestration.start()
        self._started = True


def test_embedded_runtime_satisfies_runtime_host() -> None:
    rt = EmbeddedRuntime()
    assert isinstance(rt, RuntimeHost)


def test_daemon_runtime_satisfies_runtime_host() -> None:
    rt = DaemonRuntime()
    assert isinstance(rt, RuntimeHost)


def test_definition_executor_accepts_minimal_host() -> None:
    host = _MinimalHost()
    executor = DefinitionExecutor(host)
    with pytest.raises(RuntimeError, match="Runtime host is not started"):
        executor.submit_flow(
            FlowDefinition(name="noop", pattern="wizard", options={"steps": 1}),
        )

    host.start()
    job = executor.submit_flow(
        FlowDefinition(name="noop", pattern="wizard", options={"steps": 1}),
    )
    assert job.status.value == "SUCCEEDED"
