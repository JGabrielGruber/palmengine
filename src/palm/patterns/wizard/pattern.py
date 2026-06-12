"""
WizardPattern — multi-step interactive behavior tree with events and backtracking.
"""

from __future__ import annotations

from typing import Any

from palm.core.behavior_tree import BasePattern, PatternStatus, RootNode, SequenceNode
from palm.core.context import BaseState, ContextEngine
from palm.core.event import EventEngine
from palm.core.resource import ResourceEngine
from palm.patterns.wizard.backtrack import apply_backtrack, can_backtrack_to
from palm.patterns.wizard.config import WizardConfig
from palm.patterns.wizard.events import WizardEventType
from palm.patterns.wizard.handler import CommitRegistry, default_commit_registry
from palm.patterns.wizard.keys import WizardKeys
from palm.patterns.wizard.tree import build_wizard_tree


class WizardPattern(BasePattern):
    """
    Interactive wizard with validation, summary, commit, and resource actions.

    Drive with repeated ``tick(state)`` until SUCCESS. Supply input via
    ``provide_input`` or by writing to the active step's ``input_key`` in state.
    """

    def __init__(
        self,
        *,
        name: str = "wizard",
        config: WizardConfig | None = None,
        steps: int | None = None,
        event_engine: EventEngine | None = None,
        resource_engine: ResourceEngine | None = None,
        commit_registry: CommitRegistry | None = None,
        context_engine: ContextEngine | None = None,
    ) -> None:
        super().__init__(name=name)
        if config is None:
            count = steps if steps is not None else 1
            config = WizardConfig.from_slugs([f"step_{i + 1}" for i in range(count)])
        self._config = config
        self._event_engine = event_engine
        self._resource_engine = resource_engine
        self._commit_registry = commit_registry or default_commit_registry()
        self._context_engine = context_engine
        self._root: RootNode
        self._sequence: SequenceNode
        self._root, self._sequence = build_wizard_tree(
            name,
            self._config,
            emit=self._bridge_emit,
            commit_registry=self._commit_registry,
            resource_engine=self._resource_engine,
            context_engine=self._context_engine,
        )

    @property
    def config(self) -> WizardConfig:
        return self._config

    @property
    def root(self) -> RootNode:
        return self._root

    @property
    def commit_registry(self) -> CommitRegistry:
        return self._commit_registry

    def tick(self, state: BaseState) -> PatternStatus:
        if self._context_engine is not None and self._context_engine.current_state is not state:
            self._context_engine.bind_state(state)
        if state.get(WizardKeys.COMPLETED):
            return PatternStatus.SUCCESS

        applied = apply_backtrack(state, self._root, self._sequence, self._config)
        if applied is not None:
            self._emit_event(
                WizardEventType.BACKTRACK,
                step_index=applied,
                slug=self._config.iter_tree_steps()[applied].slug,
            )

        status = self._root.tick(state)
        if status == PatternStatus.SUCCESS:
            if self._config.include_commit and not state.get(WizardKeys.COMMITTED):
                return PatternStatus.FAILURE
            state.set(WizardKeys.COMPLETED, True)
            state.set(WizardKeys.CURRENT_STEP, None)
            state.delete(WizardKeys.ACTIVE_PROMPT)
            self._emit_event(
                WizardEventType.COMPLETED,
                answers=state.get(WizardKeys.ANSWERS, {}),
                committed=bool(state.get(WizardKeys.COMMITTED)),
            )
        return status

    def reset(self) -> None:
        self._root.reset()

    def provide_input(self, state: BaseState, value: Any) -> str | None:
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
        if not self._config.allow_backtrack:
            raise ValueError("Backtracking is disabled for this wizard")
        if not can_backtrack_to(self._config, to_slug):
            self._emit_event(
                WizardEventType.BACKTRACK_BLOCKED,
                target=to_slug,
                protected=list(self._config.protected_slugs()),
            )
            raise ValueError(f"Cannot backtrack to protected step: {to_slug!r}")
        self._config.index_of(to_slug)
        state.set(WizardKeys.BACKTRACK_TO, to_slug)

    def current_step_slug(self, state: BaseState) -> str | None:
        value = state.get(WizardKeys.CURRENT_STEP)
        return str(value) if value is not None else None

    def answers(self, state: BaseState) -> dict[str, Any]:
        raw = state.get(WizardKeys.ANSWERS)
        return dict(raw) if isinstance(raw, dict) else {}

    def is_committed(self, state: BaseState) -> bool:
        return bool(state.get(WizardKeys.COMMITTED))

    def _bridge_emit(self, event_type: str, payload: dict[str, Any]) -> None:
        if self._event_engine is not None:
            self._event_engine.emit(event_type, **payload)

    def _emit_event(self, event_type: str, **payload: Any) -> None:
        self._bridge_emit(event_type, payload)


def default_wizard_config(step_count: int = 1) -> WizardConfig:
    """Factory for registry-compatible minimal wizards."""
    return WizardConfig.from_slugs([f"step_{i + 1}" for i in range(step_count)])
