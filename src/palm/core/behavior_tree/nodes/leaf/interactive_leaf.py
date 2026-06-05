"""
InteractiveLeaf — pauses the tree until external input arrives on the blackboard.

Extension point for future wizard steps. UI layers write input under
``input_key()`` before the next tick.
"""

from __future__ import annotations

from abc import abstractmethod
from typing import Any

from palm.core.behavior_tree.base_pattern import PatternStatus
from palm.core.behavior_tree.blackboard import Blackboard
from palm.core.behavior_tree.leaf import LeafNode


class InteractiveLeaf(LeafNode):
    """Abstract leaf that returns WAITING_FOR_INPUT until data is supplied."""

    INPUT_KEY_PREFIX = "__bt_input__"

    def input_key(self) -> str:
        return f"{self.INPUT_KEY_PREFIX}:{self.name}"

    def _tick_impl(self, blackboard: Blackboard) -> PatternStatus:
        key = self.input_key()
        if blackboard.has(key):
            value = blackboard.get(key)
            blackboard.delete(key)
            return self._handle_input(value, blackboard)
        return self._request_input(blackboard)

    @abstractmethod
    def _request_input(self, blackboard: Blackboard) -> PatternStatus:
        """Called when no input is present; should return WAITING_FOR_INPUT."""

    @abstractmethod
    def _handle_input(self, value: Any, blackboard: Blackboard) -> PatternStatus:
        """Process supplied input and return terminal or running status."""


class StubInteractiveLeaf(InteractiveLeaf):
    """Stub implementation for testing the interactive leaf contract."""

    def __init__(self, name: str = "test_interactive") -> None:
        super().__init__(name)
        self.received_value: Any = None

    def _request_input(self, blackboard: Blackboard) -> PatternStatus:
        blackboard.set(f"__test_prompt__:{self.name}", "Please provide input")
        return PatternStatus.WAITING_FOR_INPUT

    def _handle_input(self, value: Any, blackboard: Blackboard) -> PatternStatus:
        self.received_value = value
        blackboard.set(f"__test_received__:{self.name}", value)
        return PatternStatus.SUCCESS