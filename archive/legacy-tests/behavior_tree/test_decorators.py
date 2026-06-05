"""
Concrete decorator tests + abstract contract inheritance.
"""

from __future__ import annotations

from palm.core.behavior_tree import (
    BaseNode,
    ConditionNode,
    InverterNode,
    NodeStatus,
    RepeatNode,
)

from .test_base import AbstractNodeTest  # decorators also obey the base contract


class TestInverterNode(AbstractNodeTest):
    def create_node(self) -> BaseNode:
        child = ConditionNode("inner", predicate=lambda bb: False)
        return InverterNode("inv", child=child)

    def test_inverts_terminal_results(self, fresh_blackboard) -> None:
        true_child = ConditionNode("t", lambda bb: True)
        inv = InverterNode("inv", child=true_child)
        assert inv.tick(fresh_blackboard) == NodeStatus.FAILURE


class TestRepeatAndRetrySmoke(AbstractNodeTest):
    """Very light smoke; full behavioral tests live in integration + future dedicated files."""

    def create_node(self) -> BaseNode:
        child = ConditionNode("ok", lambda bb: True)
        return RepeatNode("rep", child=child, times=2)
