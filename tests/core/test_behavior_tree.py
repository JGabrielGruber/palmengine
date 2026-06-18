"""Tests for behavior tree engine and nodes."""

from __future__ import annotations

import pytest

from palm.core.behavior_tree import (
    ActionNode,
    BehaviorTreeEngine,
    BehaviorTreeError,
    ConditionNode,
    InvalidTreeStructureError,
    NodeExecutionError,
    PatternStatus,
    RootNode,
    SequenceNode,
)
from palm.core.context import BaseState
from palm.core.exceptions import StateNotConfiguredError
from tests.core.fakes import StubInteractiveLeaf, TestState


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


def test_engine_tick_with_no_root_returns_failure() -> None:
    engine = BehaviorTreeEngine()
    engine.initialize(state=TestState())
    assert engine.tick() == PatternStatus.FAILURE


def test_engine_set_root_revalidates_root_node(test_state: TestState) -> None:
    root = RootNode("root", child=ConditionNode("c", lambda _s: True))
    engine = BehaviorTreeEngine()
    engine.initialize(state=test_state)
    engine.set_root(root)
    assert engine.tick() == PatternStatus.SUCCESS


def test_invalid_root_structure_raises_at_construction() -> None:
    shared = ActionNode("shared", action=lambda _s: None)
    broken = SequenceNode("broken")
    broken.children.append(shared)
    broken.children.append(shared)
    shared.parent = broken

    with pytest.raises(InvalidTreeStructureError):
        RootNode("root", child=broken)


def test_engine_tick_propagates_node_execution_error(test_state: TestState) -> None:
    def boom(_s: BaseState) -> None:
        raise RuntimeError("boom")

    engine = BehaviorTreeEngine()
    engine.initialize(state=test_state)
    engine.set_root(RootNode("root", child=ActionNode("boom", boom)))

    with pytest.raises(NodeExecutionError):
        engine.tick()


def test_tick_until_terminal_stops_on_waiting_for_input(test_state: TestState) -> None:
    leaf = StubInteractiveLeaf("ask")
    engine = BehaviorTreeEngine()
    engine.initialize(state=test_state)
    engine.set_root(RootNode("root", child=leaf))

    status = engine.tick_until_terminal(max_ticks=10)
    assert status == PatternStatus.WAITING_FOR_INPUT


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
