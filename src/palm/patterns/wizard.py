"""
Wizard pattern — interactive multi-step transactional flows.

Built on ``BasePattern``; registers as ``"wizard"`` in ``pattern_registry``.
"""

from __future__ import annotations

from palm.core.behavior_tree import BasePattern, PatternStatus
from palm.core.context import BaseState
from palm.core.registry import pattern_registry


class WizardPattern(BasePattern):
    """Placeholder wizard pattern: advances until complete."""

    def __init__(self, *, name: str = "wizard", steps: int = 1) -> None:
        super().__init__(name=name)
        self._steps = steps
        self._current = 0

    def tick(self, state: BaseState) -> PatternStatus:
        if self._current >= self._steps:
            return PatternStatus.SUCCESS
        self._current += 1
        state.set("wizard_step", self._current)
        if self._current >= self._steps:
            return PatternStatus.SUCCESS
        return PatternStatus.RUNNING


pattern_registry.register("wizard", WizardPattern)