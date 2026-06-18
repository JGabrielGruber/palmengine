"""
Wizard backtracking — reset tree position with safeguards for protected steps.
"""

from __future__ import annotations

from palm.core.context import BaseState
from palm.patterns.wizard.backtrack_policy import can_backtrack_to
from palm.patterns.wizard.config import WizardConfig
from palm.patterns.wizard.keys import WizardKeys
from palm.patterns.wizard.wizard_sequence import WizardSequenceNode

__all__ = ["apply_backtrack", "can_backtrack_to"]


def apply_backtrack(
    state: BaseState,
    sequence: WizardSequenceNode,
    config: WizardConfig,
) -> int | None:
    """
    Apply a pending backtrack request via ``WizardSequenceNode``.

    Prefer letting the sequence handle backtrack during ``tick``; this helper
    remains for tests and explicit resume tooling.
    """
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