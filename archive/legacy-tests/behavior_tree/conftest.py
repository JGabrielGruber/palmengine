"""
Shared pytest fixtures for the Palm Behavior Tree test suite.

Provides reusable tree fragments, blackboards, and helper nodes so that
concrete tests stay focused on behavior rather than construction boilerplate.
"""

from __future__ import annotations

import pytest

from palm.core.behavior_tree import (
    ActionNode,
    Blackboard,
    ConditionNode,
    NodeStatus,
    SequenceNode,
)


@pytest.fixture
def fresh_blackboard() -> Blackboard:
    """A brand new, empty blackboard."""
    return Blackboard()


@pytest.fixture
def always_success() -> ConditionNode:
    """A condition that always evaluates to True."""
    return ConditionNode("always_success", predicate=lambda bb: True)


@pytest.fixture
def always_failure() -> ConditionNode:
    """A condition that always evaluates to False."""
    return ConditionNode("always_failure", predicate=lambda bb: False)


@pytest.fixture
def side_effect_counter() -> tuple[ActionNode, dict[str, int]]:
    """
    Returns (ActionNode, counter_dict).

    The action increments counter["calls"] every time it runs and returns SUCCESS.
    """
    counter: dict[str, int] = {"calls": 0}

    def increment(bb: Blackboard) -> None:
        counter["calls"] += 1
        bb.set("last_side_effect", counter["calls"])

    node = ActionNode("increment_counter", action=lambda bb: (increment(bb) or NodeStatus.SUCCESS))
    return node, counter


@pytest.fixture
def simple_success_sequence(always_success: ConditionNode) -> SequenceNode:
    """A tiny sequence that will always succeed (two conditions)."""
    return SequenceNode("success_seq", children=[always_success, always_success])
