"""Wire EventJournal append on live publish (interceptor)."""

from __future__ import annotations

from typing import TYPE_CHECKING

from palm.common.events.journal import EventJournal, compact_key_for_resource_changed
from palm.core.event import Event, EventEngine, Subscription

if TYPE_CHECKING:
    from palm.core.storage import StorageEngine

# Types that always land in the durable journal (control-plane signal).
JOURNAL_EVENT_TYPES: frozenset[str] = frozenset(
    {
        "resource.changed",
        "flow.session.succeeded",
        "flow.session.failed",
        "wizard.commit.succeeded",
        "wizard.commit.failed",
        "work.intent.enqueued",
        "work.intent.succeeded",
        "work.intent.failed",
        "job.completed",
        "job.status_changed",
    }
)


def wire_event_journal(
    event_engine: EventEngine,
    storage: StorageEngine,
    *,
    event_types: frozenset[str] | None = None,
) -> tuple[EventJournal, Subscription]:
    """
    Attach interceptor: selected live events append to the journal.

    Does not replace the outbox; both may record critical traffic.
    """
    journal = EventJournal(storage)
    allowed = event_types if event_types is not None else JOURNAL_EVENT_TYPES

    def intercept(event: Event) -> None:
        if event.type not in allowed and "*" not in allowed:
            return
        compact = None
        if event.type == "resource.changed":
            compact = compact_key_for_resource_changed(dict(event.payload))
        journal.append_event(event, compact_key=compact)

    sub = event_engine.add_interceptor(intercept)
    return journal, sub


__all__ = ["JOURNAL_EVENT_TYPES", "wire_event_journal"]
