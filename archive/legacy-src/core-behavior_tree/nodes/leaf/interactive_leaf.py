"""
InteractiveLeaf – abstract base for leaves that pause the tree for external input.

This is the primary extension point that the future Palm Wizard layer will
subclass to turn wizard steps into proper Behavior Tree nodes.

Design:
- The leaf returns WAITING_FOR_INPUT when it needs data.
- Data is supplied by the caller (wizard engine) by writing to a well-known
  blackboard key before the next tick.
- After consuming the input the leaf normally returns SUCCESS or FAILURE.

This module is part of Palm's general-purpose Behavior Tree Engine and must remain
completely independent of any wizard, UI, persistence, or domain concerns.
Higher layers (wizards) are expected to subclass this and provide concrete
input handling.

This module is part of Palm's general-purpose Behavior Tree Engine and must remain
completely independent of any wizard, UI, persistence, or domain concerns.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from ...base import Blackboard, NodeStatus
from ...leaf import LeafNode


class InteractiveLeaf(LeafNode, ABC):
    """
    Abstract base for any leaf that must pause execution until external data arrives.

    Recommended blackboard convention (used by Palm wizards later):
        key = f"__input__:{self.name}"
        # Writer (UI layer) does:
        blackboard.set(key, user_value)
        # Next tick the leaf consumes it and usually deletes the key.

    Subclasses must implement:
    - _request_input(blackboard) -> WAITING_FOR_INPUT (and optionally set metadata)
    - _handle_input(value, blackboard) -> final NodeStatus

    A minimal concrete implementation is provided for unit testing the contract
    (TestInteractiveLeaf). Real usage always involves subclassing in a domain layer.
    """

    # The conventional key prefix used for feeding input to interactive nodes.
    INPUT_KEY_PREFIX: str = "__bt_input__"

    def __init__(self, name: str) -> None:
        super().__init__(name)
        self._consumed_input: Any = None

    def input_key(self) -> str:
        """Return the blackboard key this leaf monitors for input."""
        return f"{self.INPUT_KEY_PREFIX}:{self.name}"

    def _tick_impl(self, blackboard: Blackboard) -> NodeStatus:
        key = self.input_key()
        if blackboard.has(key):
            value = blackboard.get(key)
            # Consume (remove) the input so it is not processed again
            # (we don't call clear because other keys may exist)
            if key in blackboard._data:
                del blackboard._data[key]
            return self._handle_input(value, blackboard)

        return self._request_input(blackboard)

    @abstractmethod
    def _request_input(self, blackboard: Blackboard) -> NodeStatus:
        """
        Called when no input is present.

        The implementation should:
        - Optionally write prompt / schema / choices into the blackboard
          under well-known keys (e.g. "__bt_prompt__:{name}")
        - Return NodeStatus.WAITING_FOR_INPUT
        """
        ...

    @abstractmethod
    def _handle_input(self, value: Any, blackboard: Blackboard) -> NodeStatus:
        """
        Called when input has been supplied under this leaf's input_key.

        Process the value (validation may occur in the wizard layer before
        writing to the blackboard) and return the resulting NodeStatus.
        """
        ...

    def __repr__(self) -> str:
        return f"InteractiveLeaf(name={self.name!r}, waiting={self.input_key()})"


# ----------------------------------------------------------------------
# Minimal concrete implementation used only for testing the abstract contract.
# Real interactive behavior is always provided by domain-specific subclasses.
# ----------------------------------------------------------------------


class _TestInteractiveLeaf(InteractiveLeaf):
    """
    Test double. Stores the last received value and always succeeds after input.
    Never use in production code.
    """

    def __init__(self, name: str = "test_interactive") -> None:
        super().__init__(name)
        self.received_value: Any = None

    def _request_input(self, blackboard: Blackboard) -> NodeStatus:
        blackboard.set(f"__test_prompt__:{self.name}", "Please provide input")
        return NodeStatus.WAITING_FOR_INPUT

    def _handle_input(self, value: Any, blackboard: Blackboard) -> NodeStatus:
        self.received_value = value
        blackboard.set(f"__test_received__:{self.name}", value)
        return NodeStatus.SUCCESS
