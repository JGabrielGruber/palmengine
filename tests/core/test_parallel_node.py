"""Tests for ParallelNode composite behavior."""

from __future__ import annotations

from palm.core.behavior_tree import (
    ActionNode,
    ParallelNode,
    ParallelPolicy,
    PatternStatus,
)
from palm.states import BlackboardState


def test_parallel_success_on_all() -> None:
    state = BlackboardState()
    calls: list[str] = []

    def make_action(name: str) -> ActionNode:
        def action(_state: object) -> PatternStatus:
            calls.append(name)
            return PatternStatus.SUCCESS

        return ActionNode(name, action)

    node = ParallelNode(
        "parallel",
        children=[make_action("a"), make_action("b")],
        policy=ParallelPolicy.SUCCESS_ON_ALL,
    )
    assert node.tick(state) == PatternStatus.SUCCESS
    assert sorted(calls) == ["a", "b"]


def test_parallel_success_on_any_short_circuits() -> None:
    state = BlackboardState()

    def success(_state: object) -> PatternStatus:
        return PatternStatus.SUCCESS

    def fail(_state: object) -> PatternStatus:
        return PatternStatus.FAILURE

    node = ParallelNode(
        "parallel",
        children=[
            ActionNode("win", success),
            ActionNode("lose", fail),
        ],
        policy=ParallelPolicy.SUCCESS_ON_ANY,
    )
    assert node.tick(state) == PatternStatus.SUCCESS