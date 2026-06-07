"""Tests for behavior tree engine and nodes."""

from __future__ import annotations

import pytest

from palm.core.behavior_tree import (
    ActionNode,
    BehaviorTreeEngine,
    BehaviorTreeError,
    ConditionNode,
    PatternStatus,
    RootNode,
    SelectorNode,
    SequenceNode,
)
from palm.core.context import BaseState
from palm.core.exceptions import StateNotConfiguredError
from tests.core.fakes import StubInteractiveLeaf, TestState


def test_sequence_all_success(test_state: TestState) -> None:
    tree = SequenceNode(
        "seq",
        children=[
            ConditionNode("a", lambda s: True),
            ConditionNode("b", lambda s: True),
        ],
    )
    assert tree.tick(test_state) == PatternStatus.SUCCESS


def test_sequence_fail_fast(test_state: TestState) -> None:
    tree = SequenceNode(
        "seq",
        children=[
            ConditionNode("ok", lambda s: True),
            ConditionNode("fail", lambda s: False),
        ],
    )
    assert tree.tick(test_state) == PatternStatus.FAILURE


def test_selector_first_success(test_state: TestState) -> None:
    tree = SelectorNode(
        "sel",
        children=[
            ConditionNode("fail", lambda s: False),
            ConditionNode("ok", lambda s: True),
        ],
    )
    assert tree.tick(test_state) == PatternStatus.SUCCESS


def test_action_node_writes_state(test_state: TestState) -> None:
    def mark(s: BaseState) -> None:
        s.set("done", True)

    node = ActionNode("act", action=mark)
    assert node.tick(test_state) == PatternStatus.SUCCESS
    assert test_state.get("done") is True


def test_interactive_leaf_waits_then_succeeds(test_state: TestState) -> None:
    leaf = StubInteractiveLeaf("ask")
    assert leaf.tick(test_state) == PatternStatus.WAITING_FOR_INPUT
    test_state.set(leaf.input_key(), "answer")
    assert leaf.tick(test_state) == PatternStatus.SUCCESS
    assert leaf.received_value == "answer"


def test_engine_requires_state() -> None:
    engine = BehaviorTreeEngine()
    engine.initialize()
    engine.set_root(ConditionNode("c", lambda s: True))
    with pytest.raises(StateNotConfiguredError):
        engine.tick()


def test_bt_engine_ticks_success(bt_engine: BehaviorTreeEngine) -> None:
    assert bt_engine.tick() == PatternStatus.SUCCESS


def test_tick_until_terminal_running_action(test_state: TestState) -> None:
    ticks = {"n": 0}

    def step(s: BaseState) -> PatternStatus:
        ticks["n"] += 1
        if ticks["n"] < 3:
            return PatternStatus.RUNNING
        s.set("ready", True)
        return PatternStatus.SUCCESS

    root = RootNode("root", child=ActionNode("step", step))
    engine = BehaviorTreeEngine()
    engine.initialize(state=test_state)
    engine.set_root(root)
    status = engine.tick_until_terminal(max_ticks=10)
    assert status == PatternStatus.SUCCESS
    assert ticks["n"] == 3


def test_tick_until_terminal_max_exceeded(test_state: TestState) -> None:
    root = RootNode(
        "root",
        child=ActionNode("loop", action=lambda s: PatternStatus.RUNNING),
    )
    engine = BehaviorTreeEngine()
    engine.initialize(state=test_state)
    engine.set_root(root)
    with pytest.raises(BehaviorTreeError):
        engine.tick_until_terminal(max_ticks=5)


def test_engine_reset_clears_sequence_index(test_state: TestState) -> None:
    calls = {"n": 0}

    def once(s: BaseState) -> PatternStatus:
        calls["n"] += 1
        return PatternStatus.SUCCESS if calls["n"] == 1 else PatternStatus.FAILURE

    root = RootNode(
        "root",
        child=SequenceNode("seq", children=[ActionNode("once", once)]),
    )
    engine = BehaviorTreeEngine()
    engine.initialize(state=test_state)
    engine.set_root(root)
    assert engine.tick() == PatternStatus.SUCCESS
    assert engine.tick() == PatternStatus.FAILURE
    engine.reset()
    calls["n"] = 0
    assert engine.tick() == PatternStatus.SUCCESS