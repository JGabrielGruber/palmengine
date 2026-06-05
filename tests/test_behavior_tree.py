"""Tests for behavior tree engine and nodes."""

from __future__ import annotations

import pytest

from palm.core.behavior_tree import (
    ActionNode,
    BehaviorTreeEngine,
    BehaviorTreeError,
    ConditionNode,
    InverterNode,
    PatternStatus,
    RetryNode,
    RootNode,
    SelectorNode,
    SequenceNode,
    StubInteractiveLeaf,
)
from palm.core.exceptions import StateNotConfiguredError
from palm.patterns import wizard  # noqa: F401
from palm.states import BlackboardState, TestState


@pytest.fixture
def state() -> BlackboardState:
    return BlackboardState()


def test_sequence_all_success(state: BlackboardState) -> None:
    tree = SequenceNode(
        "seq",
        children=[
            ConditionNode("a", lambda s: True),
            ConditionNode("b", lambda s: True),
        ],
    )
    assert tree.tick(state) == PatternStatus.SUCCESS


def test_sequence_fail_fast(state: BlackboardState) -> None:
    tree = SequenceNode(
        "seq",
        children=[
            ConditionNode("ok", lambda s: True),
            ConditionNode("fail", lambda s: False),
        ],
    )
    assert tree.tick(state) == PatternStatus.FAILURE


def test_selector_first_success(state: BlackboardState) -> None:
    tree = SelectorNode(
        "sel",
        children=[
            ConditionNode("fail", lambda s: False),
            ConditionNode("ok", lambda s: True),
        ],
    )
    assert tree.tick(state) == PatternStatus.SUCCESS


def test_inverter_flips_status(state: BlackboardState) -> None:
    child = ConditionNode("c", lambda s: True)
    node = InverterNode("inv", child=child)
    assert node.tick(state) == PatternStatus.FAILURE


def test_action_node_writes_state(state: BlackboardState) -> None:
    def mark(s: BlackboardState) -> None:
        s.set("done", True)

    node = ActionNode("act", action=mark)
    assert node.tick(state) == PatternStatus.SUCCESS
    assert state.get("done") is True


def test_retry_succeeds_within_attempts(state: BlackboardState) -> None:
    calls = {"n": 0}

    def flaky(s: BlackboardState) -> PatternStatus:
        calls["n"] += 1
        return PatternStatus.SUCCESS if calls["n"] >= 2 else PatternStatus.FAILURE

    node = RetryNode("retry", child=ActionNode("flaky", flaky), max_attempts=3)
    assert node.tick(state) == PatternStatus.SUCCESS
    assert calls["n"] == 2


def test_interactive_leaf_waits_then_succeeds(state: BlackboardState) -> None:
    leaf = StubInteractiveLeaf("ask")
    assert leaf.tick(state) == PatternStatus.WAITING_FOR_INPUT
    state.set(leaf.input_key(), "answer")
    assert leaf.tick(state) == PatternStatus.SUCCESS
    assert leaf.received_value == "answer"


def test_root_node_with_engine() -> None:
    root = RootNode(
        "root",
        child=ActionNode("done", action=lambda s: s.set("ok", True)),
    )
    engine = BehaviorTreeEngine()
    engine.initialize(state=BlackboardState(), root=root)
    assert engine.tick() == PatternStatus.SUCCESS
    assert engine.state.get("ok") is True


def test_engine_requires_state() -> None:
    engine = BehaviorTreeEngine()
    engine.initialize()
    engine.set_root(ConditionNode("c", lambda s: True))
    with pytest.raises(StateNotConfiguredError):
        engine.tick()


def test_tick_until_terminal_running_action() -> None:
    ticks = {"n": 0}

    def step(s: BlackboardState) -> PatternStatus:
        ticks["n"] += 1
        if ticks["n"] < 3:
            return PatternStatus.RUNNING
        s.set("ready", True)
        return PatternStatus.SUCCESS

    root = RootNode("root", child=ActionNode("step", step))
    engine = BehaviorTreeEngine()
    engine.initialize(state=BlackboardState())
    engine.set_root(root)
    status = engine.tick_until_terminal(max_ticks=10)
    assert status == PatternStatus.SUCCESS
    assert ticks["n"] == 3


def test_tick_until_terminal_max_exceeded() -> None:
    root = RootNode(
        "root",
        child=ActionNode("loop", action=lambda s: PatternStatus.RUNNING),
    )
    engine = BehaviorTreeEngine()
    engine.initialize(state=BlackboardState())
    engine.set_root(root)
    with pytest.raises(BehaviorTreeError):
        engine.tick_until_terminal(max_ticks=5)


def test_engine_reset_clears_sequence_index() -> None:
    calls = {"n": 0}

    def once(s: BlackboardState) -> PatternStatus:
        calls["n"] += 1
        return PatternStatus.SUCCESS if calls["n"] == 1 else PatternStatus.FAILURE

    root = RootNode(
        "root",
        child=SequenceNode("seq", children=[ActionNode("once", once)]),
    )
    engine = BehaviorTreeEngine()
    engine.initialize(state=BlackboardState())
    engine.set_root(root)
    assert engine.tick() == PatternStatus.SUCCESS
    assert engine.tick() == PatternStatus.FAILURE
    engine.reset()
    calls["n"] = 0
    assert engine.tick() == PatternStatus.SUCCESS


def test_wizard_pattern_via_engine() -> None:
    from palm.core import pattern_registry

    engine = BehaviorTreeEngine()
    engine.initialize(state=BlackboardState())
    cls = pattern_registry.get("wizard")
    wiz = cls(name="wiz", steps=2)
    engine.set_root(wiz)
    assert engine.tick() == PatternStatus.WAITING_FOR_INPUT
    wiz.provide_input(engine.state, "first")
    assert engine.tick() == PatternStatus.WAITING_FOR_INPUT
    wiz.provide_input(engine.state, "second")
    assert engine.tick() == PatternStatus.SUCCESS
    assert wiz.answers(engine.state)["step_1"] == "first"


def test_custom_test_state_in_tree() -> None:
    state = TestState(record=False)
    node = ActionNode("write", action=lambda s: s.set("k", "v") or None)
    node.tick(state)
    assert state.get("k") == "v"