"""
ConditionNode – a leaf that evaluates a boolean predicate against the blackboard.

SUCCESS when the predicate returns truthy, FAILURE otherwise.

This module is part of Palm's general-purpose Behavior Tree Engine and must remain
completely independent of any wizard, UI, persistence, or domain concerns.
"""

from __future__ import annotations

from collections.abc import Callable

from ...base import Blackboard, NodeStatus
from ...leaf import LeafNode


class ConditionNode(LeafNode):
    """
    Leaf node that acts as a pure predicate / guard.

    The `predicate` callable must have the signature:

        def predicate(blackboard: Blackboard) -> bool

    - Truthy return → SUCCESS
    - Falsy return  → FAILURE

    Conditions are expected to be fast and side-effect free (although the engine
    does not enforce purity). For side effects use ActionNode.

    Example:
        has_name = ConditionNode("has_name", predicate=lambda bb: bool(bb.get("user_name")))
    """

    def __init__(self, name: str, predicate: Callable[[Blackboard], bool]) -> None:
        super().__init__(name)
        if not callable(predicate):
            raise TypeError("ConditionNode requires a callable for 'predicate'")
        self._predicate = predicate

    def _tick_impl(self, blackboard: Blackboard) -> NodeStatus:
        try:
            return NodeStatus.SUCCESS if self._predicate(blackboard) else NodeStatus.FAILURE
        except Exception:
            # Let BaseNode's error wrapper turn this into NodeExecutionError
            # (keeps the original traceback as cause)
            raise

    def __repr__(self) -> str:
        return f"ConditionNode(name={self.name!r})"
