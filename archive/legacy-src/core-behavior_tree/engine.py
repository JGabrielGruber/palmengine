"""
BehaviorTree – the primary high-level controller for executing a behavior tree.

The engine owns the root and (optionally) a blackboard, and provides convenient
methods for single ticks, "run until terminal", and full resets.

This module is part of Palm's general-purpose Behavior Tree Engine and must remain
completely independent of any wizard, UI, persistence, or domain concerns.
"""

from __future__ import annotations

from .base import Blackboard, NodeStatus
from .exceptions import BehaviorTreeError, NodeExecutionError
from .root import RootNode


class BehaviorTree:
    """
    High-level executor for a complete behavior tree.

    Typical usage (non-interactive / automated flow):

        tree = BehaviorTree(my_root_node)
        status = tree.tick_until_terminal(max_ticks=10_000)
        if status == NodeStatus.SUCCESS:
            result = tree.blackboard.get("final_result")

    For interactive / wizard-style flows the caller usually drives `tick()`
    manually, inspects for WAITING_FOR_INPUT, supplies data via the blackboard,
    then continues ticking.

    The engine never auto-resets on terminal status. Call `reset()` explicitly
    when you want to re-execute the same tree.
    """

    def __init__(
        self,
        root: RootNode,
        blackboard: Blackboard | None = None,
    ) -> None:
        if not isinstance(root, RootNode):
            raise TypeError(
                "BehaviorTree requires a RootNode instance as its root. "
                "Wrap your top-level node with RootNode(name, child=...)."
            )
        self._root: RootNode = root
        self._blackboard: Blackboard = blackboard or Blackboard()
        self._last_status: NodeStatus = NodeStatus.FAILURE

        # Validate once at construction time (RootNode already did this,
        # but we keep a belt-and-suspenders call).
        self._root.validate_tree_structure()

    # ------------------------------------------------------------------
    # Primary execution API
    # ------------------------------------------------------------------

    def tick(self) -> NodeStatus:
        """
        Perform a single tick of the entire tree.

        Returns the status returned by the root node. The caller is responsible
        for deciding whether to continue, pause, or supply input.
        """
        try:
            self._last_status = self._root.tick(self._blackboard)
            return self._last_status
        except NodeExecutionError:
            # Already well-wrapped by the node layer
            raise
        except Exception as exc:
            # Extremely defensive top-level safety net
            raise BehaviorTreeError(f"Unexpected error during BehaviorTree.tick: {exc}") from exc

    def tick_until_terminal(self, max_ticks: int = 10_000) -> NodeStatus:
        """
        Repeatedly call tick() until the tree reaches a terminal status
        (SUCCESS, FAILURE) or WAITING_FOR_INPUT.

        RUNNING nodes cause the loop to continue.

        Raises BehaviorTreeError if the tree fails to terminate after max_ticks.
        This is a safeguard against infinite loops in misbehaving trees.
        """
        if max_ticks < 1:
            raise ValueError("max_ticks must be >= 1")

        for _ in range(max_ticks):
            status = self.tick()
            if status not in (NodeStatus.RUNNING, NodeStatus.WAITING_FOR_INPUT):
                return status

        raise BehaviorTreeError(
            f"Behavior tree did not reach a terminal or waiting state after {max_ticks} ticks. "
            f"Last status: {self._last_status}. Possible infinite loop or missing reset."
        )

    def reset(self) -> None:
        """Reset the entire tree (including all internal node state) and clear last status."""
        self._root.reset()
        self._last_status = NodeStatus.FAILURE

    # ------------------------------------------------------------------
    # Introspection
    # ------------------------------------------------------------------

    @property
    def root(self) -> RootNode:
        """The RootNode that heads this tree."""
        return self._root

    @property
    def blackboard(self) -> Blackboard:
        """The blackboard instance used by this tree execution."""
        return self._blackboard

    @property
    def last_status(self) -> NodeStatus:
        """The status returned by the most recent call to tick()."""
        return self._last_status

    def __repr__(self) -> str:
        return (
            f"BehaviorTree(root={self._root.name!r}, "
            f"last_status={self._last_status}, "
            f"bb_keys={len(self._blackboard.keys())})"
        )
