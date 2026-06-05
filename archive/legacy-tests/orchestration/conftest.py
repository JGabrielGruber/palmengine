"""
Shared pytest fixtures for the Orchestration Engine test suite.

These fixtures are deliberately pure (TestMode + TestBackend only).
The single optional BT integration test imports its own BT fixtures.
"""

from __future__ import annotations

import pytest

from palm.core.events import Event, EventBus
from palm.core.orchestration import (
    Blackboard,  # independent data carrier (tests may still use BT objects in the single integration test)
    Orchestrator,
    TestMode,
)


@pytest.fixture
def test_mode() -> TestMode:
    """A fresh TestMode (primary mode for all core contract tests)."""
    mode = TestMode()
    mode.start()
    return mode


@pytest.fixture
def orchestrator(test_mode: TestMode) -> Orchestrator:
    """Orchestrator pre-wired with TestMode (the recommended test setup)."""
    orch = Orchestrator(mode=test_mode)
    orch.start()
    return orch


@pytest.fixture
def fresh_blackboard() -> Blackboard:
    """Empty blackboard (still the canonical data carrier even with TestBackend)."""
    return Blackboard()


@pytest.fixture
def event_collector() -> tuple[EventBus, list[Event]]:
    """
    Returns (bus, collected_events list).

    Subscribes to all common orchestration events for assertions.
    """
    bus = EventBus()
    collected: list[Event] = []

    def collector(event: Event) -> None:
        collected.append(event)

    for name in [
        "orchestrator.started",
        "orchestrator.shutdown",
        "job.submitted",
        "job.status_changed",
        "job.completed",
        "job.input_received",
        "job.cancelled",
    ]:
        bus.subscribe(name, collector)

    return bus, collected


@pytest.fixture
def sample_test_work() -> dict[str, object]:
    """A simple successful work descriptor for TestBackend."""
    return {"steps": 2, "final_status": "SUCCEEDED", "result": "ok"}


@pytest.fixture
def waiting_test_work() -> dict[str, object]:
    """A work descriptor that goes to WAITING_FOR_INPUT."""
    return {"steps": 1, "final_status": "WAITING_FOR_INPUT"}
