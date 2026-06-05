"""
Concrete tests for composite nodes, inheriting the abstract contract tests.
"""

from __future__ import annotations

from palm.core.behavior_tree import (
    BaseNode,
    Blackboard,
    ConditionNode,
    NodeStatus,
    ParallelNode,
    SelectorNode,
    SequenceNode,
)

from .test_base import AbstractCompositeTest


class TestSequenceNode(AbstractCompositeTest):
    def create_node(self) -> BaseNode:
        c = ConditionNode("always_true", predicate=lambda bb: True)
        return SequenceNode("test_seq", children=[c])

    def create_node_with_children(self, children: list[BaseNode]) -> BaseNode:
        return SequenceNode("seq", children=children)

    def test_empty_sequence_is_success(self, fresh_blackboard: Blackboard) -> None:
        seq = SequenceNode("empty")
        assert seq.tick(fresh_blackboard) == NodeStatus.SUCCESS

    def test_fail_fast_on_first_failure(self, fresh_blackboard: Blackboard) -> None:
        seq = SequenceNode(
            "mixed",
            children=[
                ConditionNode("ok", lambda bb: True),
                ConditionNode("fail", lambda bb: False),
                ConditionNode("never", lambda bb: True),
            ],
        )
        assert seq.tick(fresh_blackboard) == NodeStatus.FAILURE


class TestSelectorNode(AbstractCompositeTest):
    def create_node(self) -> BaseNode:
        c = ConditionNode("true", predicate=lambda bb: True)
        return SelectorNode("sel", children=[c])

    def create_node_with_children(self, children: list[BaseNode]) -> BaseNode:
        return SelectorNode("sel", children=children)

    def test_empty_selector_is_failure(self, fresh_blackboard: Blackboard) -> None:
        sel = SelectorNode("empty")
        assert sel.tick(fresh_blackboard) == NodeStatus.FAILURE


class TestParallelNode(AbstractCompositeTest):
    def create_node(self) -> BaseNode:
        c = ConditionNode("true", predicate=lambda bb: True)
        return ParallelNode("par", children=[c])

    def create_node_with_children(self, children: list[BaseNode]) -> BaseNode:
        return ParallelNode("par", children=children)

    def test_parallel_success_on_all(self, fresh_blackboard: Blackboard) -> None:
        p = ParallelNode(
            "p",
            children=[
                ConditionNode("a", lambda bb: True),
                ConditionNode("b", lambda bb: True),
            ],
        )
        assert p.tick(fresh_blackboard) == NodeStatus.SUCCESS
