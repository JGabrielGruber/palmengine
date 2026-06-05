"""
Tests for the high-level BehaviorTree engine (tick, tick_until_terminal, reset, safety).
"""

from __future__ import annotations

import pytest

from palm.core.behavior_tree import (
    ActionNode,
    BehaviorTree,
    Blackboard,
    ConditionNode,
    NodeStatus,
    RootNode,
    SequenceNode,
)
from palm.core.behavior_tree.exceptions import BehaviorTreeError


def test_behavior_tree_basic_happy_path() -> None:
    def set_done(bb: Blackboard) -> None:
        bb.set("done", True)

    cond = ConditionNode("not_done", predicate=lambda bb: not bb.get("done", False))
    action = ActionNode("mark_done", action=lambda bb: (set_done(bb) or NodeStatus.SUCCESS))

    seq = SequenceNode("work", children=[cond, action])
    root = RootNode("root", child=seq)
    tree = BehaviorTree(root)

    status = tree.tick_until_terminal()
    assert status == NodeStatus.SUCCESS
    assert tree.blackboard.get("done") is True


def test_behavior_tree_reset_allows_re_execution() -> None:
    calls: list[int] = []

    def record(bb: Blackboard) -> NodeStatus:
        calls.append(1)
        return NodeStatus.SUCCESS

    action = ActionNode("record", action=record)
    root = RootNode("r", child=action)
    tree = BehaviorTree(root)

    tree.tick_until_terminal()
    assert len(calls) == 1

    tree.reset()
    tree.tick_until_terminal()
    assert len(calls) == 2


def test_behavior_tree_max_ticks_guard() -> None:
    # A node that always returns RUNNING will trigger the guard
    runner = ActionNode("runner", action=lambda bb: NodeStatus.RUNNING)
    root = RootNode("loop", child=runner)
    tree = BehaviorTree(root)

    with pytest.raises(BehaviorTreeError, match="did not reach a terminal"):
        tree.tick_until_terminal(max_ticks=5)


def test_behavior_tree_wraps_unexpected_errors() -> None:
    def boom(bb: Blackboard) -> None:
        raise RuntimeError("intentional crash")

    action = ActionNode("crash", action=boom)
    root = RootNode("root", child=action)
    tree = BehaviorTree(root)

    with pytest.raises(Exception) as exc:  # NodeExecutionError or subclass
        tree.tick()
    assert "crash" in str(exc.value) or "intentional" in str(exc.value)
