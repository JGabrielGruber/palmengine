"""
WizardSequenceNode — sequence composite with backtrack and resume support.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from palm.core.behavior_tree import RootNode, SequenceNode
from palm.core.behavior_tree.base_pattern import PatternStatus
from palm.core.context import BaseState
from palm.patterns.wizard.backtrack_policy import can_backtrack_to
from palm.patterns.wizard.config import WizardConfig
from palm.patterns.wizard.keys import WizardKeys

BacktrackNotifier = Callable[[int, BaseState, str, Any], None]


class WizardSequenceNode(SequenceNode):
    """
    Ordered wizard steps with integrated backtrack handling.

    Reads ``WizardKeys.BACKTRACK_TO`` before each tick, resets the subtree,
    and jumps to the requested index. Exposes :meth:`jump_to_index` for resume
    and persistence instead of mutating private sequence state elsewhere.
    """

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
        """Move execution to ``index`` without resetting child subtrees."""
        if index < 0 or index >= len(self.children):
            raise IndexError(f"Wizard step index out of range: {index}")
        self._current_index = index

    def restore_position(self, state: BaseState, index: int) -> None:
        """Align sequence index and wizard state after resume."""
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