"""Tests for RuntimeHost protocol decoupling."""

from __future__ import annotations

import pytest

from palm.core.event import EventEngine
from palm.core.orchestration import OrchestrationEngine
from palm.definitions.flow import FlowDefinition
from palm.executions import DefinitionExecutor
from palm.runtimes.daemon import DaemonRuntime
from palm.runtimes.embedded import EmbeddedRuntime
from palm.runtimes.host import RuntimeHost
from palm.runtimes.schedulers import InlineScheduler
from tests.core.fakes.runner import TestRunner


class _MinimalHost:
    """Lightweight runtime double for executions-layer tests."""

    def __init__(self) -> None:
        self.orchestration = OrchestrationEngine()
        self.event = EventEngine()
        self.resource = None
        self._started = False

    @property
    def is_started(self) -> bool:
        return self._started

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