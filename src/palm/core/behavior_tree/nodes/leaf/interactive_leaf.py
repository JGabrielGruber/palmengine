"""
InteractiveLeaf — pauses the tree until external input arrives on state.

Extension point for future wizard steps. UI layers write input under
``input_key()`` before the next tick.
"""

from __future__ import annotations

from abc import abstractmethod
from typing import Any

from palm.core.behavior_tree.base_pattern import PatternStatus
from palm.core.behavior_tree.leaf import LeafNode
from palm.core.context import BaseState


class InteractiveLeaf(LeafNode):
    """Abstract leaf that returns WAITING_FOR_INPUT until data is supplied."""

    INPUT_KEY_PREFIX = "__bt_input__"
    PROMPT_KEY_PREFIX = "__bt_prompt__"

    def input_key(self) -> str:
        return f"{self.INPUT_KEY_PREFIX}:{self.name}"

    def prompt_key(self) -> str:
        """Blackboard key where this leaf publishes prompt metadata."""
        return f"{self.PROMPT_KEY_PREFIX}:{self.name}"

    def _tick_impl(self, state: BaseState) -> PatternStatus:
        key = self.input_key()
        if state.has(key):
            value = state.get(key)
            state.delete(key)
            return self._handle_input(value, state)
        return self._request_input(state)

    @abstractmethod
    def _request_input(self, state: BaseState) -> PatternStatus:
        """Called when no input is present; should return WAITING_FOR_INPUT."""

    @abstractmethod
    def _handle_input(self, value: Any, state: BaseState) -> PatternStatus:
        """Process supplied input and return terminal or running status."""
