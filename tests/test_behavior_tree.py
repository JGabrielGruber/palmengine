"""Tests for behavior tree engine and nodes."""

from __future__ import annotations

import pytest

from palm.core.behavior_tree import (
    ActionNode,
    BehaviorTreeEngine,
    BehaviorTreeError,
    Blackboard,
    ConditionNode,
    InverterNode,
    PatternStatus,
    RetryNode,
    RootNode,
    SelectorNode,
    SequenceNode,
    StubInteractiveLeaf,
)
from palm.patterns import wizard  # noqa: F401


@pytest.fixture
def blackboard() -> Blackboard:
    return Blackboard()


def test_sequence_all_success(blackboard: Blackboard) -> None:
    tree = SequenceNode(
        "seq",
        children=[
            ConditionNode("a", lambda bb: True),
            ConditionNode("b", lambda bb: True),
        ],
    )
    assert tree.tick(blackboard) == PatternStatus.SUCCESS


def test_sequence_fail_fast(blackboard: Blackboard) -> None:
    tree = SequenceNode(
        "seq",
        children=[
            ConditionNode("ok", lambda bb: True),
            ConditionNode("fail", lambda bb: False),
        ],
    )
    assert tree.tick(blackboard) == PatternStatus.FAILURE


def test_selector_first_success(blackboard: Blackboard) -> None:
    tree = SelectorNode(
        "sel",
        children=[
            ConditionNode("fail", lambda bb: False),
            ConditionNode("ok", lambda bb: True),
        ],
    )
    assert tree.tick(blackboard) == PatternStatus.SUCCESS


def test_inverter_flips_status(blackboard: Blackboard) -> None:
    child = ConditionNode("c", lambda bb: True)
    node = InverterNode("inv", child=child)
    assert node.tick(blackboard) == PatternStatus.FAILURE


def test_action_node_writes_blackboard(blackboard: Blackboard) -> None:
    def mark(bb: Blackboard) -> None:
        bb.set("done", True)

    node = ActionNode("act", action=mark)
    assert node.tick(blackboard) == PatternStatus.SUCCESS
    assert blackboard.get("done") is True


def test_retry_succeeds_within_attempts(blackboard: Blackboard) -> None:
    calls = {"n": 0}

    def flaky(bb: Blackboard) -> PatternStatus:
        calls["n"] += 1
        return PatternStatus.SUCCESS if calls["n"] >= 2 else PatternStatus.FAILURE

    node = RetryNode("retry", child=ActionNode("flaky", flaky), max_attempts=3)
    assert node.tick(blackboard) == PatternStatus.SUCCESS
    assert calls["n"] == 2


def test_interactive_leaf_waits_then_succeeds(blackboard: Blackboard) -> None:
    leaf = StubInteractiveLeaf("ask")
    assert leaf.tick(blackboard) == PatternStatus.WAITING_FOR_INPUT
    blackboard.set(leaf.input_key(), "answer")
    assert leaf.tick(blackboard) == PatternStatus.SUCCESS
    assert leaf.received_value == "answer"


def test_root_node_with_engine() -> None:
    root = RootNode(
        "root",
        child=ActionNode("done", action=lambda bb: bb.set("ok", True)),
    )
    engine = BehaviorTreeEngine()
    engine.initialize(root=root)
    assert engine.tick() == PatternStatus.SUCCESS
    assert engine.blackboard.get("ok") is True


def test_tick_until_terminal_running_action() -> None:
    ticks = {"n": 0}

    def step(bb: Blackboard) -> PatternStatus:
        ticks["n"] += 1
        if ticks["n"] < 3:
            return PatternStatus.RUNNING
        bb.set("ready", True)
        return PatternStatus.SUCCESS

    root = RootNode("root", child=ActionNode("step", step))
    engine = BehaviorTreeEngine()
    engine.set_root(root)
    status = engine.tick_until_terminal(max_ticks=10)
    assert status == PatternStatus.SUCCESS
    assert ticks["n"] == 3


def test_tick_until_terminal_max_exceeded() -> None:
    root = RootNode(
        "root",
        child=ActionNode("loop", action=lambda bb: PatternStatus.RUNNING),
    )
    engine = BehaviorTreeEngine()
    engine.set_root(root)
    with pytest.raises(BehaviorTreeError):
        engine.tick_until_terminal(max_ticks=5)


def test_engine_reset_clears_sequence_index(blackboard: Blackboard) -> None:
    calls = {"n": 0}

    def once(bb: Blackboard) -> PatternStatus:
        calls["n"] += 1
        return PatternStatus.SUCCESS if calls["n"] == 1 else PatternStatus.FAILURE

    root = RootNode(
        "root",
        child=SequenceNode("seq", children=[ActionNode("once", once)]),
    )
    engine = BehaviorTreeEngine()
    engine.set_root(root)
    assert engine.tick() == PatternStatus.SUCCESS
    assert engine.tick() == PatternStatus.FAILURE
    engine.reset()
    calls["n"] = 0
    assert engine.tick() == PatternStatus.SUCCESS


def test_wizard_pattern_via_engine() -> None:
    from palm.core import pattern_registry

    engine = BehaviorTreeEngine()
    engine.initialize()
    cls = pattern_registry.get("wizard")
    engine.set_root(cls(name="wiz", steps=2))
    assert engine.tick() == PatternStatus.RUNNING
    assert engine.tick() == PatternStatus.SUCCESS
    assert engine.blackboard.get("wizard_step") == 2