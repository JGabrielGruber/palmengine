"""
WizardPattern — multi-step interactive behavior tree with events and backtracking.
"""

from __future__ import annotations

from typing import Any

from palm.core.behavior_tree import BasePattern, PatternStatus, RootNode, SequenceNode
from palm.core.context import BaseState
from palm.core.event import EventEngine
from palm.patterns.wizard.backtrack import apply_backtrack
from palm.patterns.wizard.config import WizardConfig
from palm.patterns.wizard.events import WizardEventType
from palm.patterns.wizard.keys import WizardKeys
from palm.patterns.wizard.tree import build_wizard_tree


class WizardPattern(BasePattern):
    """
    Interactive wizard built from ``RootNode`` → ``SequenceNode`` → ``WizardStepLeaf``.

    Drive with repeated ``tick(state)`` until SUCCESS. Supply input via
    ``provide_input`` or by writing to the active step's ``input_key`` in state.
    Use ``request_backtrack`` to revisit an earlier step when allowed.
    """

    def __init__(
        self,
        *,
        name: str = "wizard",
        config: WizardConfig | None = None,
        steps: int | None = None,
        event_engine: EventEngine | None = None,
    ) -> None:
        super().__init__(name=name)
        if config is None:
            count = steps if steps is not None else 1
            config = WizardConfig.from_slugs([f"step_{i + 1}" for i in range(count)])
        self._config = config
        self._event_engine = event_engine
        self._root: RootNode
        self._sequence: SequenceNode
        self._root, self._sequence = build_wizard_tree(
            name,
            self._config,
            emit=self._bridge_emit,
        )

    @property
    def config(self) -> WizardConfig:
        return self._config

    @property
    def root(self) -> RootNode:
        return self._root

    def tick(self, state: BaseState) -> PatternStatus:
        if state.get(WizardKeys.COMPLETED):
            return PatternStatus.SUCCESS

        applied = apply_backtrack(state, self._root, self._sequence, self._config)
        if applied is not None:
            self._emit_event(
                WizardEventType.BACKTRACK,
                step_index=applied,
                slug=self._config.steps[applied].slug,
            )

        status = self._root.tick(state)
        if status == PatternStatus.SUCCESS:
            state.set(WizardKeys.COMPLETED, True)
            state.set(WizardKeys.CURRENT_STEP, None)
            state.delete(WizardKeys.ACTIVE_PROMPT)
            self._emit_event(
                WizardEventType.COMPLETED,
                answers=state.get(WizardKeys.ANSWERS, {}),
            )
        return status

    def reset(self) -> None:
        self._root.reset()

    def provide_input(self, state: BaseState, value: Any) -> str | None:
        """
        Write input for the current waiting step.

        Returns the slug that received input, or ``None`` if no step is waiting.
        """
        prompt = state.get(WizardKeys.ACTIVE_PROMPT)
        if not isinstance(prompt, dict):
            return None
        input_key = prompt.get("input_key")
        if not isinstance(input_key, str):
            return None
        state.set(input_key, value)
        slug = prompt.get("slug")
        return str(slug) if slug is not None else None

    def request_backtrack(self, state: BaseState, to_slug: str) -> None:
        """Schedule backtracking to ``to_slug`` on the next tick."""
        if not self._config.allow_backtrack:
            raise ValueError("Backtracking is disabled for this wizard")
        self._config.index_of(to_slug)  # validate slug exists
        state.set(WizardKeys.BACKTRACK_TO, to_slug)

    def current_step_slug(self, state: BaseState) -> str | None:
        value = state.get(WizardKeys.CURRENT_STEP)
        return str(value) if value is not None else None

    def answers(self, state: BaseState) -> dict[str, Any]:
        raw = state.get(WizardKeys.ANSWERS)
        return dict(raw) if isinstance(raw, dict) else {}

    def _bridge_emit(self, event_type: str, payload: dict[str, Any]) -> None:
        """Adapt step-leaf emitter signature to ``EventEngine.emit``."""
        if self._event_engine is not None:
            self._event_engine.emit(event_type, **payload)

    def _emit_event(self, event_type: str, **payload: Any) -> None:
        self._bridge_emit(event_type, payload)


def default_wizard_config(step_count: int = 1) -> WizardConfig:
    """Factory for registry-compatible minimal wizards."""
    return WizardConfig.from_slugs([f"step_{i + 1}" for i in range(step_count)])