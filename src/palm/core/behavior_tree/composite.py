"""CompositeNode abstract base — nodes with one or more children."""

from __future__ import annotations

from abc import ABC

from palm.core.behavior_tree.base import BaseNode
from palm.core.behavior_tree.exceptions import InvalidTreeStructureError


class CompositeNode(BaseNode, ABC):
    """Abstract base for composite (multi-child) nodes."""

    def __init__(self, name: str, children: list[BaseNode] | None = None) -> None:
        super().__init__(name)
        if children:
            for child in children:
                self._add_child(child)

    def _validate_child_count(self) -> None:
        if len(self.children) < 1:
            raise InvalidTreeStructureError(
                f"{self.__class__.__name__} {self.name!r} must have at least one child"
            )
