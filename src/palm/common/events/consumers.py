"""
Named journal consumers (0.40.3).

Standard names for lag observability and catch-up helpers:

- ``work_drain`` — deferred WorkIntent path (offsets for ops; drain still uses store)
- ``webhooks`` — external delivery catch-up from journal
- ``projections`` — rebuild/catch-up projections from journal

Consumers advance **their own** offsets via :meth:`EventJournal.consume`.
"""

from __future__ import annotations

from typing import Any, Callable

from palm.common.events.journal import EventJournal, JournalEntry

# Canonical names used in host.control_plane_status / doctor
JOURNAL_CONSUMER_WORK_DRAIN = "work_drain"
JOURNAL_CONSUMER_WEBHOOKS = "webhooks"
JOURNAL_CONSUMER_PROJECTIONS = "projections"

DEFAULT_JOURNAL_CONSUMERS: tuple[str, ...] = (
    JOURNAL_CONSUMER_WORK_DRAIN,
    JOURNAL_CONSUMER_WEBHOOKS,
    JOURNAL_CONSUMER_PROJECTIONS,
)

# Event types typically interesting for each consumer
WEBHOOK_EVENT_TYPES: frozenset[str] = frozenset(
    {
        "resource.changed",
        "flow.session.succeeded",
        "flow.session.failed",
        "wizard.commit.succeeded",
        "job.completed",
        "job.status_changed",
    }
)

PROJECTION_EVENT_TYPES: frozenset[str] = frozenset(
    {
        "resource.changed",
        "flow.session.succeeded",
        "flow.session.failed",
        "wizard.commit.succeeded",
        "wizard.commit.failed",
        "job.completed",
        "job.status_changed",
        "work.intent.enqueued",
        "work.intent.succeeded",
        "work.intent.failed",
    }
)


def journal_consumer_status(
    journal: EventJournal,
    *,
    consumers: list[str] | tuple[str, ...] | None = None,
) -> dict[str, Any]:
    """Lag snapshot for doctor / control_plane."""
    names = list(consumers) if consumers is not None else list(DEFAULT_JOURNAL_CONSUMERS)
    return journal.status(consumers=names)


def consume_for_webhooks(
    journal: EventJournal,
    on_entry: Callable[[JournalEntry], None],
    *,
    limit: int = 50,
    auto_commit: bool = True,
    event_types: frozenset[str] | None = None,
    consumer: str = JOURNAL_CONSUMER_WEBHOOKS,
) -> list[JournalEntry]:
    """
    Drain journal for webhook-style side effects.

    ``on_entry`` should deliver one event externally; raise to leave offset uncommitted
    when ``auto_commit`` is False (caller controls commit).
    """
    types = event_types if event_types is not None else WEBHOOK_EVENT_TYPES
    batch = journal.consume(
        consumer,
        limit=limit,
        event_types=types,
        auto_commit=False,
    )
    delivered: list[JournalEntry] = []
    for entry in batch:
        on_entry(entry)
        delivered.append(entry)
        if auto_commit:
            journal.commit_consumer_offset(consumer, entry.offset)
    return delivered


def consume_for_projections(
    journal: EventJournal,
    on_entry: Callable[[JournalEntry], None],
    *,
    limit: int = 50,
    auto_commit: bool = True,
    event_types: frozenset[str] | None = None,
    consumer: str = JOURNAL_CONSUMER_PROJECTIONS,
) -> list[JournalEntry]:
    """Drain journal for projection catch-up handlers."""
    types = event_types if event_types is not None else PROJECTION_EVENT_TYPES
    batch = journal.consume(
        consumer,
        limit=limit,
        event_types=types,
        auto_commit=False,
    )
    applied: list[JournalEntry] = []
    for entry in batch:
        on_entry(entry)
        applied.append(entry)
        if auto_commit:
            journal.commit_consumer_offset(consumer, entry.offset)
    return applied


def mark_work_drain_caught_up(journal: EventJournal) -> int:
    """
    Advance ``work_drain`` consumer to latest journal offset.

    Work drain uses WorkIntentStore for execution; this offset is **observability**
    (and optional redrive coordination), not the claim queue.
    """
    latest = journal.latest_offset()
    journal.commit_consumer_offset(JOURNAL_CONSUMER_WORK_DRAIN, latest)
    return latest


__all__ = [
    "DEFAULT_JOURNAL_CONSUMERS",
    "JOURNAL_CONSUMER_PROJECTIONS",
    "JOURNAL_CONSUMER_WEBHOOKS",
    "JOURNAL_CONSUMER_WORK_DRAIN",
    "PROJECTION_EVENT_TYPES",
    "WEBHOOK_EVENT_TYPES",
    "consume_for_projections",
    "consume_for_webhooks",
    "journal_consumer_status",
    "mark_work_drain_caught_up",
]
