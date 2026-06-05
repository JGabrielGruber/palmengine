"""
Palm Behavior Tree specific exceptions.

All exceptions inherit from PalmError so that callers can catch the broad
`palm.exceptions.PalmError` while still allowing fine-grained handling
of tree construction vs. runtime execution failures.

This module is part of Palm's general-purpose Behavior Tree Engine and must remain
completely independent of any wizard, UI, persistence, or domain concerns.
"""

from __future__ import annotations

from palm.exceptions import PalmError


class BehaviorTreeError(PalmError):
    """
    Base exception for all errors that originate inside the Behavior Tree Engine.

    This is the class users of the engine should primarily catch when they want
    to handle "something went wrong while ticking a tree".
    """

    def __init__(self, message: str, *, code: str | None = None) -> None:
        super().__init__(message, code=code or "BEHAVIOR_TREE_ERROR")


class InvalidTreeStructureError(BehaviorTreeError):
    """
    Raised exclusively during tree construction / validation.

    Examples:
    - Attempting to create a cycle
    - Adding more than one child to a DecoratorNode
    - Adding any child to a LeafNode
    - A composite ending up with zero children when it requires ≥1
    - A node that already has a parent being added again
    """

    def __init__(self, message: str) -> None:
        super().__init__(message, code="INVALID_TREE_STRUCTURE")


class NodeExecutionError(BehaviorTreeError):
    """
    Wraps any unexpected exception thrown from inside a node's `_tick_impl`,
    `_setup`, or user-supplied callables (ActionNode, Condition predicates, etc.).

    The original exception is preserved as `__cause__`. The message includes
    the name of the node that failed to aid debugging.
    """

    def __init__(self, message: str) -> None:
        super().__init__(message, code="NODE_EXECUTION_ERROR")
