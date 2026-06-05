"""
Base types for the Palm Behavior Tree Engine.

This module defines the fundamental abstractions used by every node in the tree:
- NodeStatus (SUCCESS, FAILURE, RUNNING, WAITING_FOR_INPUT)
- Blackboard (the single source of truth for all data sharing)
- BaseNode (abstract root of the node hierarchy with tick/reset/contract enforcement)

This module is part of Palm's general-purpose Behavior Tree Engine and must remain
completely independent of any wizard, UI, persistence, or domain concerns.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from enum import StrEnum
from typing import Any

from .exceptions import (
    BehaviorTreeError,
    InvalidTreeStructureError,
    NodeExecutionError,
)


class NodeStatus(StrEnum):
    """
    Possible return values from any Behavior Tree node tick.

    Semantics (standard BT + Palm extensions):
    - SUCCESS: The node completed its goal successfully.
    - FAILURE: The node was unable to achieve its goal.
    - RUNNING: The node has started long-running work and needs future ticks to continue.
    - WAITING_FOR_INPUT: The node is paused pending external data (e.g. user input).
      Higher-level layers (wizards) use this to pause the entire tree until the UI
      supplies a value via the blackboard.

    RUNNING and WAITING_FOR_INPUT are treated identically by composites for control
    flow (they do not advance past the node), but WAITING_FOR_INPUT carries extra
    semantic meaning for interactive scenarios.
    """

    SUCCESS = "SUCCESS"
    FAILURE = "FAILURE"
    RUNNING = "RUNNING"
    WAITING_FOR_INPUT = "WAITING_FOR_INPUT"


class Blackboard:
    """
    Shared memory used by all nodes in a behavior tree.

    Design principles:
    - All inter-node communication happens exclusively through the blackboard.
    - Nodes are responsible for key hygiene (prefix keys with node name or category).
    - The implementation is deliberately minimal and explicit.
    - Future extensions (namespacing, typed accessors, change listeners) can be
      added without changing the public get/set/has/clear contract.

    Thread safety: Not provided. Higher layers (Orchestrator) manage concurrency.
    """

    def __init__(self) -> None:
        self._data: dict[str, Any] = {}

    def get(self, key: str, default: Any = None) -> Any:
        """Return the value for key, or default if absent."""
        return self._data.get(key, default)

    def set(self, key: str, value: Any) -> None:
        """Store value under key (overwrites if present)."""
        self._data[key] = value

    def has(self, key: str) -> bool:
        """Return True if key exists in the blackboard."""
        return key in self._data

    def clear(self) -> None:
        """Remove all entries. Use with extreme caution in running trees."""
        self._data.clear()

    def snapshot(self) -> dict[str, Any]:
        """Return a shallow copy of the entire blackboard (primarily for debugging/tests)."""
        return dict(self._data)

    def keys(self) -> list[str]:
        """Return list of all current keys (for inspection)."""
        return list(self._data.keys())

    def __repr__(self) -> str:
        return f"Blackboard(keys={len(self._data)})"


class BaseNode(ABC):
    """
    Abstract base class for every node in a Palm Behavior Tree.

    Responsibilities (SRP):
    - Own a stable name and parent/child relationships.
    - Provide the public `tick(blackboard)` contract.
    - Enforce tree structural integrity (parent uniqueness, cycle prevention).
    - Support explicit state reset for stateful nodes (sequences, retries, etc.).

    Subclassing rules:
    - Leaf nodes inherit from LeafNode (not directly from BaseNode).
    - Composites and decorators inherit from their respective ABCs.
    - All concrete nodes must implement `_tick_impl`.

    The public `tick` method performs setup, error translation, and status validation.
    Subclasses should override `_tick_impl` (and optionally `_reset_impl` / `_setup`).
    """

    def __init__(self, name: str) -> None:
        if not name or not isinstance(name, str):
            raise ValueError("Node name must be a non-empty string")
        self.name: str = name
        self.parent: BaseNode | None = None
        self.children: list[BaseNode] = []
        self._setup_done: bool = False

    # ------------------------------------------------------------------
    # Core tick contract
    # ------------------------------------------------------------------

    @abstractmethod
    def _tick_impl(self, blackboard: Blackboard) -> NodeStatus:
        """
        Perform the actual work of the node.

        This method is called by the public `tick` wrapper. It must:
        - Return a valid NodeStatus member.
        - Never raise raw exceptions (wrap via the public tick error handling).
        - Use only the provided blackboard for data (no instance state for inter-tick
          data that should survive reset; use `_reset_impl` for internal counters).
        """
        ...

    def tick(self, blackboard: Blackboard) -> NodeStatus:
        """
        Execute one tick of this node (and its subtree).

        This is the primary entry point called by parents and the BehaviorTree engine.
        It guarantees:
        - One-time `_setup` call before the first real tick.
        - All exceptions from `_tick_impl` (or setup) are converted to NodeExecutionError.
        - Returned status is always a valid NodeStatus.
        """
        try:
            if not self._setup_done:
                self._setup(blackboard)
                self._setup_done = True

            status = self._tick_impl(blackboard)

            if not isinstance(status, NodeStatus):
                # Defensive: coerce or fail loudly
                raise NodeExecutionError(
                    f"Node '{self.name}' returned non-NodeStatus value: {status!r}"
                )
            return status

        except BehaviorTreeError:
            # Re-raise our own errors without wrapping
            raise
        except Exception as exc:
            raise NodeExecutionError(
                f"Unhandled exception in node '{self.name}' during tick: {exc}"
            ) from exc

    # ------------------------------------------------------------------
    # Lifecycle hooks (override as needed)
    # ------------------------------------------------------------------

    def _setup(self, blackboard: Blackboard) -> None:
        """Called exactly once before the first tick. Override for initialization."""
        pass

    def _reset_impl(self) -> None:
        """
        Reset any node-local mutable state (counters, indices, caches).

        Called by the public `reset()`. The base implementation does nothing;
        stateful nodes (Sequence, Retry, etc.) must override this.
        """
        pass

    def reset(self) -> None:
        """
        Fully reset this node and its entire subtree.

        After reset the tree can be ticked again as if it had never run.
        All internal indices/counters must be cleared by `_reset_impl`.
        """
        self._setup_done = False
        self._reset_impl()
        for child in self.children:
            child.reset()

    # ------------------------------------------------------------------
    # Tree construction & validation (called by composites/decorators/root)
    # ------------------------------------------------------------------

    def _add_child(self, child: BaseNode) -> None:
        """
        Attach a child node.

        Enforces:
        - A node may have at most one parent (strict tree semantics).
        - No cycles are introduced.
        """
        if child.parent is not None:
            raise InvalidTreeStructureError(
                f"Node '{child.name}' already has a parent ('{child.parent.name}'). "
                "Shared subtrees are not allowed in the current Palm BT model."
            )

        # Walk up our own ancestor chain to detect cycles
        ancestor: BaseNode | None = self
        while ancestor is not None:
            if ancestor is child:
                raise InvalidTreeStructureError(
                    f"Cycle detected: cannot add '{child.name}' as a descendant of '{self.name}'"
                )
            ancestor = ancestor.parent

        child.parent = self
        self.children.append(child)

    def validate_tree_structure(self) -> None:
        """
        Perform a full DFS validation of the tree rooted at this node.

        Raises InvalidTreeStructureError on any violation.
        Called automatically by RootNode, BehaviorTree, and composite constructors.
        """
        seen: set[int] = set()
        self._validate_recursive(seen)

    def _validate_recursive(self, seen: set[int]) -> None:
        node_id = id(self)
        if node_id in seen:
            raise InvalidTreeStructureError(
                f"Duplicate node or cycle detected involving '{self.name}'"
            )
        seen.add(node_id)
        for child in self.children:
            child._validate_recursive(seen)

    # ------------------------------------------------------------------
    # Introspection / debugging
    # ------------------------------------------------------------------

    def __repr__(self) -> str:
        child_names = [c.name for c in self.children]
        return f"{self.__class__.__name__}(name={self.name!r}, children={child_names})"
