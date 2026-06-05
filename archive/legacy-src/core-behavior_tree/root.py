"""
RootNode – the official entry point wrapper for any Behavior Tree.

A RootNode is a very thin decorator-like node whose only job is to give the
tree a single, well-known root object that the BehaviorTree engine can rely on.
It also centralizes top-level validation.

This module is part of Palm's general-purpose Behavior Tree Engine and must remain
completely independent of any wizard, UI, persistence, or domain concerns.
"""

from __future__ import annotations

from .base import BaseNode, Blackboard, NodeStatus
from .decorator import DecoratorNode


class RootNode(DecoratorNode):
    """
    The canonical root of a behavior tree.

    Usage:
        root = RootNode("my_tree_root", child=some_composite_or_leaf)
        bt = BehaviorTree(root)

    A RootNode is a DecoratorNode with exactly one child. It performs no
    special transformation of the child's status — it simply forwards it.
    Its value lies in providing a stable, named anchor and guaranteeing that
    `validate_tree_structure()` has been called on the entire tree.

    You may also tick a RootNode directly (without BehaviorTree) if you manage
    your own blackboard.
    """

    def __init__(self, name: str, child: BaseNode) -> None:
        # Force the child through the decorator contract
        super().__init__(name, child=child)
        # Immediately validate the whole tree we now root
        self.validate_tree_structure()

    def _tick_impl(self, blackboard: Blackboard) -> NodeStatus:
        """Simply delegate to the single child."""
        return self.child.tick(blackboard)

    # We do not override reset — the base Decorator + BaseNode recursion is sufficient.
