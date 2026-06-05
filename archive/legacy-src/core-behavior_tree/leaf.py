"""
LeafNode abstract base class.

Leaves are the "action" or "condition" nodes of the tree — they contain no children
and perform the actual work or predicate evaluation.

This module is part of Palm's general-purpose Behavior Tree Engine and must remain
completely independent of any wizard, UI, persistence, or domain concerns.
"""

from __future__ import annotations

from abc import ABC

from .base import BaseNode


class LeafNode(BaseNode, ABC):
    """
    Abstract base for all leaf nodes (nodes that perform work and have zero children).

    Contract enforced:
    - A LeafNode may never have children added (attempts raise InvalidTreeStructureError).
    - Subclasses implement only `_tick_impl(blackboard) -> NodeStatus`.

    Typical subclasses: ActionNode, ConditionNode, and domain-specific interactive leaves.
    """

    def __init__(self, name: str) -> None:
        super().__init__(name)
        # Leaves start with an empty children list that must stay empty.

    def _add_child(self, child: BaseNode) -> None:
        """Leaves are forbidden from having children."""
        from .exceptions import InvalidTreeStructureError

        raise InvalidTreeStructureError(
            f"LeafNode '{self.name}' cannot have children. " f"Attempted to add '{child.name}'."
        )

    # The abstract _tick_impl is inherited from BaseNode.
    # Concrete leaves implement it directly.
