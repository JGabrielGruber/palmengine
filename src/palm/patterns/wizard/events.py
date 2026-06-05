"""
Wizard event type constants for ``EventEngine``.
"""

from __future__ import annotations


class WizardEventType:
    STEP_STARTED = "wizard.step.started"
    INPUT_RECEIVED = "wizard.input.received"
    BACKTRACK = "wizard.backtrack"
    COMPLETED = "wizard.completed"