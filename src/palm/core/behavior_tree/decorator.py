"""DecoratorNode abstract base — nodes wrapping exactly one child."""

from __future__ import annotations

from abc import ABC

from palm.core.behavior_tree.base import BaseNode
from palm.core.behavior_tree.exceptions import InvalidTreeStructureError


class DecoratorNode(BaseNode, ABC):
    """Abstract base for decorator nodes (single child)."""

    def __init__(self, name: str, child: BaseNode | None = None) -> None:
        super().__init__(name)
        if child is not None:
            self._add_child(child)

    @property
    def child(self) -> BaseNode:
        if not self.children:
            raise InvalidTreeStructureError(f"Decorator {self.name!r} has no child")
        return self.children[0]

    def _add_child(self, child: BaseNode) -> None:
        if self.children:
            raise InvalidTreeStructureError(
                f"Decorator {self.name!r} already has child {self.children[0].name!r}"
            )
        super()._add_child(child)

    def _validate_child_count(self) -> None:
        if len(self.children) != 1:
            raise InvalidTreeStructureError(
                f"{self.__class__.__name__} {self.name!r} must have exactly one child "
                f"(has {len(self.children)})"
            )
