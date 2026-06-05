"""
Wizard event type constants for ``EventEngine``.
"""

from __future__ import annotations


class WizardEventType:
    STEP_STARTED = "wizard.step.started"
    INPUT_RECEIVED = "wizard.input.received"
    BACKTRACK = "wizard.backtrack"
    BACKTRACK_BLOCKED = "wizard.backtrack.blocked"
    VALIDATION_FAILED = "wizard.validation.failed"
    SUMMARY_SHOWN = "wizard.summary.shown"
    COMMIT_STARTED = "wizard.commit.started"
    COMMIT_SUCCEEDED = "wizard.commit.succeeded"
    COMMIT_FAILED = "wizard.commit.failed"
    ACTION_EXECUTED = "wizard.action.executed"
    COMPLETED = "wizard.completed"