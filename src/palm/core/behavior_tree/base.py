"""
Base node types for the Palm Behavior Tree engine.

Defines ``BaseNode`` — the root of the node hierarchy with tick/reset contracts.
"""

from __future__ import annotations

from abc import abstractmethod
from typing import TYPE_CHECKING

from palm.core.behavior_tree.base_pattern import BasePattern, PatternStatus
from palm.core.behavior_tree.blackboard import Blackboard
from palm.core.behavior_tree.exceptions import (
    BehaviorTreeError,
    InvalidTreeStructureError,
    NodeExecutionError,
)

if TYPE_CHECKING:
    pass


class BaseNode(BasePattern):
    """
    Abstract base for behavior tree nodes with parent/child structure.

    Subclasses implement ``_tick_impl``. The public ``tick`` wrapper performs
    setup, error translation, and status validation.
    """

    def __init__(self, name: str) -> None:
        super().__init__(name=name)
        self.parent: BaseNode | None = None
        self.children: list[BaseNode] = []
        self._setup_done = False

    @abstractmethod
    def _tick_impl(self, blackboard: Blackboard) -> PatternStatus:
        """Perform the node's work. Called by ``tick``."""

    def tick(self, blackboard: Blackboard) -> PatternStatus:
        try:
            if not self._setup_done:
                self._setup(blackboard)
                self._setup_done = True
            status = self._tick_impl(blackboard)
            if not isinstance(status, PatternStatus):
                raise NodeExecutionError(
                    f"Node {self.name!r} returned non-PatternStatus value: {status!r}"
                )
            return status
        except BehaviorTreeError:
            raise
        except Exception as exc:
            raise NodeExecutionError(
                f"Unhandled exception in node {self.name!r} during tick: {exc}"
            ) from exc

    def _setup(self, blackboard: Blackboard) -> None:
        pass

    def _reset_impl(self) -> None:
        pass

    def reset(self) -> None:
        self._setup_done = False
        self._reset_impl()
        for child in self.children:
            child.reset()

    def _add_child(self, child: BaseNode) -> None:
        if child.parent is not None:
            raise InvalidTreeStructureError(
                f"Node {child.name!r} already has parent {child.parent.name!r}"
            )
        ancestor: BaseNode | None = self
        while ancestor is not None:
            if ancestor is child:
                raise InvalidTreeStructureError(
                    f"Cycle detected: cannot add {child.name!r} under {self.name!r}"
                )
            ancestor = ancestor.parent
        child.parent = self
        self.children.append(child)

    def validate_tree_structure(self) -> None:
        seen: set[int] = set()
        self._validate_recursive(seen)

    def _validate_recursive(self, seen: set[int]) -> None:
        node_id = id(self)
        if node_id in seen:
            raise InvalidTreeStructureError(
                f"Duplicate node or cycle detected involving {self.name!r}"
            )
        seen.add(node_id)
        for child in self.children:
            child._validate_recursive(seen)

    def __repr__(self) -> str:
        child_names = [c.name for c in self.children]
        return f"{self.__class__.__name__}(name={self.name!r}, children={child_names})"