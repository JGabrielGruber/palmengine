"""
Compensation trigger event names — string constants only (no pattern imports).
"""

from __future__ import annotations


class CompensationTrigger:
    """Domain events that may invoke registered compensation handlers."""

    COMMIT_FAILED = "wizard.commit.failed"
    COMMIT_STARTED = "wizard.commit.started"
    BACKTRACK_EXECUTED = "wizard.backtrack.executed"


class CompensationEventType:
    """Observability events emitted by the compensation coordinator."""

    EXECUTED = "compensation.executed"
    FAILED = "compensation.failed"
    SKIPPED = "compensation.skipped"