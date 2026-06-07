"""
Fixtures for pure ``palm.core`` engine tests.

Uses test doubles from :mod:`tests.core.fakes` only — never production shortcuts
inside ``palm.core``. Pattern- or runtime-specific tests belong in ``tests/`` or
future ``tests/patterns/``, ``tests/executions/``, etc.
"""

from __future__ import annotations

from collections.abc import Iterator

import pytest

from palm.core.behavior_tree import BehaviorTreeEngine, RootNode
from palm.core.behavior_tree.nodes import ActionNode
from palm.core.context import ContextEngine
from palm.core.event import EventEngine
from palm.core.orchestration import OrchestrationEngine
from tests.core.fakes import TestState
from tests.core.fakes.mode import TestMode


@pytest.fixture
def test_state() -> TestState:
    """Fresh :class:`TestState` — the canonical blackboard double for core tests."""
    return TestState()


@pytest.fixture
def test_mode() -> TestMode:
    """Synchronous orchestration mode backed by :class:`~tests.core.fakes.backend.TestBackend`."""
    mode = TestMode()
    mode.start()
    return mode


@pytest.fixture
def context_engine() -> Iterator[ContextEngine]:
    """Initialized context engine; shut down after the test."""
    engine = ContextEngine()
    engine.initialize()
    yield engine
    engine.shutdown()


@pytest.fixture
def event_engine() -> Iterator[EventEngine]:
    """Initialized event bus; shut down after the test."""
    engine = EventEngine()
    engine.initialize()
    yield engine
    engine.shutdown()


@pytest.fixture
def bt_engine(test_state: TestState) -> Iterator[BehaviorTreeEngine]:
    """Behavior tree engine with a trivial always-success root."""
    engine = BehaviorTreeEngine()
    root = RootNode(
        "root",
        child=ActionNode("noop", action=lambda _s: None),
    )
    engine.initialize(state=test_state, root=root)
    yield engine
    engine.shutdown()


@pytest.fixture
def orchestration_engine(test_mode: TestMode) -> Iterator[OrchestrationEngine]:
    """Orchestration engine wired with :class:`TestMode`."""
    engine = OrchestrationEngine()
    engine.initialize(mode=test_mode)
    engine.start()
    yield engine
    engine.stop()
    engine.shutdown()


@pytest.fixture
def full_core_setup(
    test_state: TestState,
    test_mode: TestMode,
) -> Iterator[dict[str, object]]:
    """All core engines initialized and cross-wired for contract-level integration tests."""
    ctx = ContextEngine()
    events = EventEngine()
    bt = BehaviorTreeEngine()
    orch = OrchestrationEngine()

    ctx.initialize(state=test_state)
    events.initialize()
    orch.initialize(mode=test_mode, event_engine=events, context_engine=ctx)
    bt.initialize(state=test_state)
    orch.start()

    bundle = {
        "test_state": test_state,
        "context_engine": ctx,
        "event_engine": events,
        "bt_engine": bt,
        "orchestration_engine": orch,
        "test_mode": test_mode,
    }
    yield bundle

    orch.stop()
    orch.shutdown()
    bt.shutdown()
    ctx.shutdown()
    events.shutdown()