"""
Wizard state key conventions — shared between pattern, tests, and future UI.
"""

from __future__ import annotations


class WizardKeys:
    """Well-known keys written into ``BaseState`` during wizard execution."""

    PREFIX = "__wizard__"
    ANSWERS = f"{PREFIX}.answers"
    CURRENT_STEP = f"{PREFIX}.current_step"
    ACTIVE_PROMPT = f"{PREFIX}.active_prompt"
    BACKTRACK_TO = f"{PREFIX}.backtrack_to"
    COMPLETED = f"{PREFIX}.completed"
    STEP_INDEX = f"{PREFIX}.step_index"
    COMMITTED = f"{PREFIX}.committed"
    COMMIT_ERROR = f"{PREFIX}.commit_error"
    COMMIT_RESULT = f"{PREFIX}.commit_result"
    VALIDATION_ERROR = f"{PREFIX}.validation_error"
    VALIDATION_ERRORS = f"{PREFIX}.validation_errors"
    SUMMARY_ACK = f"{PREFIX}.summary_ack"
    RESOURCE_RESULT = f"{PREFIX}.resource_result"
