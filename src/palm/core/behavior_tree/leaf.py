"""LeafNode abstract base — nodes with no children."""

from __future__ import annotations

from abc import ABC

from palm.core.behavior_tree.base import BaseNode
from palm.core.behavior_tree.exceptions import InvalidTreeStructureError


class LeafNode(BaseNode, ABC):
    """Abstract base for leaf nodes."""

    def __init__(self, name: str) -> None:
        super().__init__(name)

    def _add_child(self, child: BaseNode) -> None:
        raise InvalidTreeStructureError(
            f"LeafNode {self.name!r} cannot have children (attempted {child.name!r})"
        )