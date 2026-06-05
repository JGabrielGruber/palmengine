"""
Wizard backtracking — reset tree position and restore step index in state.
"""

from __future__ import annotations

from palm.core.behavior_tree import RootNode, SequenceNode
from palm.core.context import BaseState
from palm.patterns.wizard.config import WizardConfig
from palm.patterns.wizard.keys import WizardKeys


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
    elif isinstance(target, str):
        index = config.index_of(target)
    else:
        return None

    if index < 0 or index >= config.step_count:
        return None

    root.reset()
    sequence._current_index = index
    state.set(WizardKeys.STEP_INDEX, index)
    state.set(WizardKeys.CURRENT_STEP, config.steps[index].slug)
    state.delete(WizardKeys.ACTIVE_PROMPT)
    return index