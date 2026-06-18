"""
Wizard backtrack and completion phases — sequence navigation inside the BT.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from palm.core.behavior_tree import DecoratorNode, RootNode, SequenceNode
from palm.core.behavior_tree.base_pattern import PatternStatus
from palm.core.context import BaseState
from palm.patterns.wizard.config import WizardConfig
from palm.patterns.wizard.events import WizardEventType
from palm.patterns.wizard.keys import WizardKeys
from palm.patterns.wizard.leaf_support import EventEmitter, emit_wizard_event

BacktrackNotifier = Callable[[int, BaseState, str, Any], None]


def can_backtrack_to(config: WizardConfig, target: str | int) -> bool:
    """Return whether backtracking to ``target`` (slug or index) is allowed."""
    if not config.allow_backtrack:
        return False

    slug = target if isinstance(target, str) else config.iter_tree_steps()[target].slug
    if slug in config.protected_slugs():
        return False

    step = config.get_step(slug)
    if step is not None and step.is_protected:
        return False
    return True


def request_backtrack(
    state: BaseState,
    config: WizardConfig,
    to_slug: str,
    *,
    emit: EventEmitter | None = None,
    wizard_name: str | None = None,
) -> None:
    """Queue a backtrack target; applied on the next sequence tick."""
    if not config.allow_backtrack:
        raise ValueError("Backtracking is disabled for this wizard")
    if not can_backtrack_to(config, to_slug):
        emit_wizard_event(
            emit,
            wizard_name or "wizard",
            WizardEventType.BACKTRACK_BLOCKED,
            target=to_slug,
            protected=list(config.protected_slugs()),
        )
        raise ValueError(f"Cannot backtrack to protected step: {to_slug!r}")
    config.index_of(to_slug)
    emit_wizard_event(
        emit,
        wizard_name or "wizard",
        WizardEventType.BACKTRACK_REQUESTED,
        from_step=state.get(WizardKeys.CURRENT_STEP),
        to_slug=to_slug,
    )
    state.set(WizardKeys.BACKTRACK_TO, to_slug)


class WizardSequenceNode(SequenceNode):
    """Ordered wizard steps with integrated backtrack handling."""

    def __init__(
        self,
        name: str,
        *,
        config: WizardConfig,
        children: list | None = None,
        on_backtrack: BacktrackNotifier | None = None,
    ) -> None:
        super().__init__(name, children=children)
        self._config = config
        self._on_backtrack = on_backtrack

    @property
    def current_index(self) -> int:
        return self._current_index

    def jump_to_index(self, index: int) -> None:
        if index < 0 or index >= len(self.children):
            raise IndexError(f"Wizard step index out of range: {index}")
        self._current_index = index

    def restore_position(self, state: BaseState, index: int) -> None:
        self.jump_to_index(index)
        steps = self._config.iter_tree_steps()
        state.set(WizardKeys.STEP_INDEX, index)
        state.set(WizardKeys.CURRENT_STEP, steps[index].slug)

    def _tick_impl(self, state: BaseState) -> PatternStatus:
        from_step = state.get(WizardKeys.CURRENT_STEP)
        applied = self._apply_backtrack(state)
        if applied is not None and self._on_backtrack is not None:
            slug = self._config.iter_tree_steps()[applied].slug
            self._on_backtrack(applied, state, slug, from_step)
        return super()._tick_impl(state)

    def _apply_backtrack(self, state: BaseState) -> int | None:
        if not self._config.allow_backtrack:
            state.delete(WizardKeys.BACKTRACK_TO)
            return None

        target = state.get(WizardKeys.BACKTRACK_TO)
        if target is None:
            return None

        state.delete(WizardKeys.BACKTRACK_TO)
        index, slug = self._resolve_backtrack_target(target)
        if index is None or slug is None:
            return None
        if not can_backtrack_to(self._config, slug):
            return None

        self._reset_for_backtrack(state, index, slug)
        return index

    def _resolve_backtrack_target(self, target: Any) -> tuple[int | None, str | None]:
        tree_steps = self._config.iter_tree_steps()
        if isinstance(target, int):
            if target < 0 or target >= len(tree_steps):
                return None, None
            return target, tree_steps[target].slug
        if isinstance(target, str):
            if not can_backtrack_to(self._config, target):
                return None, None
            return self._config.index_of(target), target
        return None, None

    def _reset_for_backtrack(self, state: BaseState, index: int, slug: str) -> None:
        root = self._find_root()
        if root is not None:
            root.reset()
        self.jump_to_index(index)
        state.set(WizardKeys.STEP_INDEX, index)
        state.set(WizardKeys.CURRENT_STEP, slug)
        state.delete(WizardKeys.ACTIVE_PROMPT)

    def _find_root(self) -> RootNode | None:
        node: Any = self
        while node.parent is not None:
            node = node.parent
        return node if isinstance(node, RootNode) else None


def apply_backtrack(
    state: BaseState,
    sequence: WizardSequenceNode,
    config: WizardConfig,
) -> int | None:
    """Explicitly apply a pending backtrack (tests and resume tooling)."""
    if not config.allow_backtrack:
        state.delete(WizardKeys.BACKTRACK_TO)
        return None

    target = state.get(WizardKeys.BACKTRACK_TO)
    if target is None:
        return None

    index, slug = sequence._resolve_backtrack_target(target)  # noqa: SLF001
    if index is None or slug is None:
        state.delete(WizardKeys.BACKTRACK_TO)
        return None

    state.delete(WizardKeys.BACKTRACK_TO)
    sequence._reset_for_backtrack(state, index, slug)  # noqa: SLF001
    return index


class WizardCompletionGuardNode(DecoratorNode):
    """Wraps the wizard step sequence and applies completion invariants."""

    def __init__(
        self,
        name: str,
        *,
        child: SequenceNode,
        config: WizardConfig,
        emit: EventEmitter | None = None,
        wizard_name: str = "wizard",
    ) -> None:
        super().__init__(name, child=child)
        self._config = config
        self._emit = emit
        self._wizard_name = wizard_name

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
        emit_wizard_event(
            self._emit,
            self._wizard_name,
            WizardEventType.COMPLETED,
            answers=state.get(WizardKeys.ANSWERS, {}),
            committed=bool(state.get(WizardKeys.COMMITTED)),
        )
        return PatternStatus.SUCCESS


def backtrack_notifier(emit: EventEmitter, wizard_name: str) -> BacktrackNotifier:
    def notify(index: int, state: BaseState, slug: str, from_step: object) -> None:
        payload = {
            "wizard": wizard_name,
            "step_index": index,
            "slug": slug,
            "from_step": from_step,
            "to_slug": slug,
        }
        emit(WizardEventType.BACKTRACK, payload)
        emit(WizardEventType.BACKTRACK_EXECUTED, payload)

    return notify