"""
Fixtures for pure ``palm.core`` engine tests.

Orchestration tests use :class:`~tests.core.fakes.mode.TestMode` and
:class:`~tests.core.fakes.backend.TestBackend` — never production core code.
"""

from __future__ import annotations

from collections.abc import Iterator

import pytest

from palm.core.behavior_tree import BehaviorTreeEngine, RootNode
from palm.core.behavior_tree.nodes import ActionNode
from palm.core.context import ContextEngine
from palm.core.event import EventEngine
from palm.core.orchestration import OrchestrationEngine
from palm.states import BlackboardState
from tests.core.fakes.mode import TestMode


@pytest.fixture
def blackboard_state() -> BlackboardState:
    """Fresh blackboard for behavior-tree and orchestration tests."""
    return BlackboardState()


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
def bt_engine(blackboard_state: BlackboardState) -> Iterator[BehaviorTreeEngine]:
    """Behavior tree engine with a trivial always-success root."""
    engine = BehaviorTreeEngine()
    root = RootNode(
        "root",
        child=ActionNode("noop", action=lambda _s: None),
    )
    engine.initialize(state=blackboard_state, root=root)
    yield engine
    engine.shutdown()


@pytest.fixture
def orchestration_engine() -> Iterator[OrchestrationEngine]:
    """Orchestration engine wired with :class:`TestMode` (synchronous test driver)."""
    engine = OrchestrationEngine()
    engine.initialize(mode=TestMode())
    engine.start()
    yield engine
    engine.stop()
    engine.shutdown()


@pytest.fixture
def full_core_setup(
    blackboard_state: BlackboardState,
) -> Iterator[dict[str, object]]:
    """All core engines initialized and cross-wired for integration-style core tests."""
    ctx = ContextEngine()
    events = EventEngine()
    bt = BehaviorTreeEngine()
    orch = OrchestrationEngine()

    ctx.initialize(state=blackboard_state)
    events.initialize()
    orch.initialize(mode=TestMode(), event_engine=events, context_engine=ctx)
    bt.initialize(state=blackboard_state)
    orch.start()

    bundle = {
        "blackboard_state": blackboard_state,
        "context_engine": ctx,
        "event_engine": events,
        "bt_engine": bt,
        "orchestration_engine": orch,
    }
    yield bundle

    orch.stop()
    orch.shutdown()
    bt.shutdown()
    ctx.shutdown()
    events.shutdown()