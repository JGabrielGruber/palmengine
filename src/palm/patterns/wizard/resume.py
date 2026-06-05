"""
Wizard resume helpers — restore tree position from persisted state.
"""

from __future__ import annotations

from palm.core.context import BaseState
from palm.patterns.wizard.keys import WizardKeys
from palm.patterns.wizard.pattern import WizardPattern


def restore_wizard_position(wizard: WizardPattern, state: BaseState) -> None:
    """
    Align the behavior tree with ``state`` after loading a snapshot.

    Sets the sequence index from ``WizardKeys.STEP_INDEX`` so resumed wizards
    continue at the correct step with answers intact.
    """
    index = state.get(WizardKeys.STEP_INDEX)
    if isinstance(index, int) and index >= 0:
        steps = wizard.config.iter_tree_steps()
        if index < len(steps):
            wizard._sequence._current_index = index
            state.set(WizardKeys.CURRENT_STEP, steps[index].slug)


def wizard_runtime_position(wizard: WizardPattern, state: BaseState) -> dict[str, int | str | None]:
    """Capture BT position metadata for instance persistence."""
    index = state.get(WizardKeys.STEP_INDEX)
    slug = state.get(WizardKeys.CURRENT_STEP)
    return {
        "sequence_index": index if isinstance(index, int) else wizard._sequence._current_index,
        "current_step": str(slug) if slug is not None else None,
    }
