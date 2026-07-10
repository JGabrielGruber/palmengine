"""
Cross-cutting domain event names for reliable publishing.
"""

from __future__ import annotations

from palm.core.orchestration.events import OrchestrationEventType


class DomainEventType:
    """Events that should be durably recorded via the outbox."""

    INSTANCE_CREATED = OrchestrationEventType.INSTANCE_CREATED
    INSTANCE_STATUS_CHANGED = OrchestrationEventType.INSTANCE_STATUS_CHANGED
    WIZARD_STEP_COMPLETED = "wizard.step.completed"
    BACKTRACK_EXECUTED = "wizard.backtrack.executed"


CRITICAL_EVENT_TYPES: frozenset[str] = frozenset(
    {
        DomainEventType.WIZARD_STEP_COMPLETED,
        DomainEventType.BACKTRACK_EXECUTED,
        "wizard.backtrack",
        "wizard.commit.started",
        "wizard.commit.succeeded",
        "wizard.commit.failed",
        "job.status_changed",
        "job.completed",
        "wizard.completed",
        "resource.changed",
        "flow.session.succeeded",
        "flow.session.failed",
        "work.intent.enqueued",
        "work.intent.succeeded",
        "work.intent.failed",
    }
)

INSTANCE_EVENT_TYPES: frozenset[str] = frozenset(
    {
        DomainEventType.INSTANCE_CREATED,
        DomainEventType.INSTANCE_STATUS_CHANGED,
    }
)
