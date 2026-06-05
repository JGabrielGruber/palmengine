"""
DecoratorNode abstract base class.

Decorators wrap exactly one child and modify its result or control its execution
(Inverter, Retry, Repeat, Timeout, ForceSuccess, etc.).

This module is part of Palm's general-purpose Behavior Tree Engine and must remain
completely independent of any wizard, UI, persistence, or domain concerns.
"""

from __future__ import annotations

from abc import ABC

from .base import BaseNode
from .exceptions import InvalidTreeStructureError


class DecoratorNode(BaseNode, ABC):
    """
    Abstract base for all decorator nodes (nodes that wrap exactly one child).

    Contract:
    - Must have exactly one child at the moment the tree is validated / ticked.
    - The single child is exposed as the convenience property `child`.

    Decorators are the mechanism for adding cross-cutting behavior (negation,
    repetition, error recovery) without polluting the child node.
    """

    def __init__(self, name: str, child: BaseNode | None = None) -> None:
        super().__init__(name)
        if child is not None:
            self._add_child(child)

    @property
    def child(self) -> BaseNode:
        """Return the single decorated child (raises if not present)."""
        if not self.children:
            raise InvalidTreeStructureError(
                f"Decorator '{self.name}' has no child. Decorators require exactly one child."
            )
        return self.children[0]

    def _add_child(self, child: BaseNode) -> None:
        """Decorators are limited to exactly one child."""
        if self.children:
            raise InvalidTreeStructureError(
                f"DecoratorNode '{self.name}' already has a child. "
                f"Cannot add second child '{child.name}'."
            )
        super()._add_child(child)

    def _validate_child_count(self) -> None:
        """Ensure exactly one child exists at validation time."""
        if len(self.children) != 1:
            raise InvalidTreeStructureError(
                f"{self.__class__.__name__} '{self.name}' must have exactly one child "
                f"(has {len(self.children)})."
            )
