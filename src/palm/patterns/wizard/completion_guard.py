"""
WizardCompletionGuardNode — terminal completion checks inside the behavior tree.
"""

from __future__ import annotations

from typing import Any

from palm.core.behavior_tree import BaseNode, DecoratorNode, PatternStatus
from palm.core.context import BaseState
from palm.patterns.wizard.config import WizardConfig
from palm.patterns.wizard.events import WizardEventType
from palm.patterns.wizard.keys import WizardKeys
from palm.patterns.wizard.step_leaf import EventEmitter


class WizardCompletionGuardNode(DecoratorNode):
    """
    Wraps the wizard step sequence and applies completion invariants.

    When the child sequence succeeds, enforces commit requirements and marks the
    wizard complete. This keeps ``WizardPattern.tick`` thin and makes completion
    behavior visible in the tree structure.
    """

    def __init__(
        self,
        name: str,
        *,
        child: BaseNode,
        config: WizardConfig,
        emit: EventEmitter | None = None,
    ) -> None:
        super().__init__(name, child=child)
        self._config = config
        self._emit = emit

    def _tick_impl(self, state: BaseState) -> PatternStatus:
        if state.get(WizardKeys.COMPLETED):
            return PatternStatus.SUCCESS

        status = self.child.tick(state)
        if status != PatternStatus.SUCCESS:
            return status

        if self._config.include_commit and not state.get(WizardKeys.COMMITTED):
            return PatternStatus.FAILURE

        state.set(WizardKeys.COMPLETED, True)
        state.set(WizardKeys.CURRENT_STEP, None)
        state.delete(WizardKeys.ACTIVE_PROMPT)
        self._emit_completed(state)
        return PatternStatus.SUCCESS

    def _emit_completed(self, state: BaseState) -> None:
        if self._emit is None:
            return
        self._emit(
            WizardEventType.COMPLETED,
            {
                "answers": state.get(WizardKeys.ANSWERS, {}),
                "committed": bool(state.get(WizardKeys.COMMITTED)),
            },
        )