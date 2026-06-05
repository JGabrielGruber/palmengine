"""
CompositeNode abstract base class.

Composites are nodes that contain one or more children and define control-flow
semantics (Sequence = "AND", Selector = "OR", Parallel, etc.).

This module is part of Palm's general-purpose Behavior Tree Engine and must remain
completely independent of any wizard, UI, persistence, or domain concerns.
"""

from __future__ import annotations

from abc import ABC

from .base import BaseNode
from .exceptions import InvalidTreeStructureError


class CompositeNode(BaseNode, ABC):
    """
    Abstract base for all composite nodes (nodes that contain ≥1 children).

    Responsibilities:
    - Enforce "at least one child" at construction time.
    - Provide common helper behavior for child iteration and state reset.
    - Subclasses (Sequence, Selector, Parallel) implement the specific traversal policy
      inside `_tick_impl`.

    Composites are the primary vehicle for building complex control flow.
    """

    def __init__(self, name: str, children: list[BaseNode] | None = None) -> None:
        super().__init__(name)
        if children:
            for child in children:
                self._add_child(child)

        # Subclasses may still add children after construction via _add_child,
        # but the final tree must be validated by RootNode / BehaviorTree.

    def _add_child(self, child: BaseNode) -> None:
        """Allow addition but enforce that composites always end up with ≥1 child (checked at validation)."""
        super()._add_child(child)

    def _validate_child_count(self) -> None:
        """Called by concrete composites that require a minimum child count."""
        if len(self.children) < 1:
            raise InvalidTreeStructureError(
                f"{self.__class__.__name__} '{self.name}' must have at least one child."
            )
