"""
Wizard backtracking — reset tree position with safeguards for protected steps.
"""

from __future__ import annotations

from palm.core.behavior_tree import RootNode, SequenceNode
from palm.core.context import BaseState
from palm.patterns.wizard.config import WizardConfig
from palm.patterns.wizard.keys import WizardKeys


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


def apply_backtrack(
    state: BaseState,
    root: RootNode,
    sequence: SequenceNode,
    config: WizardConfig,
) -> int | None:
    """
    If ``WizardKeys.BACKTRACK_TO`` is set, reset the tree and jump to that step.

    Returns the target step index when backtrack was applied, else ``None``.
    """
    if not config.allow_backtrack:
        state.delete(WizardKeys.BACKTRACK_TO)
        return None

    target = state.get(WizardKeys.BACKTRACK_TO)
    if target is None:
        return None

    state.delete(WizardKeys.BACKTRACK_TO)
    if isinstance(target, int):
        index = target
        slug = config.iter_tree_steps()[index].slug
    elif isinstance(target, str):
        if not can_backtrack_to(config, target):
            return None
        index = config.index_of(target)
        slug = target
    else:
        return None

    tree_steps = config.iter_tree_steps()
    if index < 0 or index >= len(tree_steps):
        return None

    if not can_backtrack_to(config, slug):
        return None

    root.reset()
    sequence._current_index = index
    state.set(WizardKeys.STEP_INDEX, index)
    state.set(WizardKeys.CURRENT_STEP, tree_steps[index].slug)
    state.delete(WizardKeys.ACTIVE_PROMPT)
    return index
