"""
Public Palm event catalog (0.42).

These types are safe to stream to authorized consumers (Portal, palm provider).
Payloads should stay **small** (refs, ids, hashes) — not full documents.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

# Align with journal wire defaults (control-plane signal).
PUBLIC_EVENT_TYPES: frozenset[str] = frozenset(
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
        "inbound.received",
    }
)

# Recommended for composition (wait / react) — subset of public.
COMPOSITION_EVENT_TYPES: frozenset[str] = frozenset(
    {
        "resource.changed",
        "flow.session.succeeded",
        "flow.session.failed",
        "job.completed",
        "job.status_changed",
        "inbound.received",
    }
)


@dataclass(frozen=True)
class EventTypeInfo:
    type: str
    category: str
    summary: str
    composition: bool = False


_CATALOG: tuple[EventTypeInfo, ...] = (
    EventTypeInfo(
        "resource.changed",
        "resource",
        "Mutating resource invoke succeeded (ref + action; no body)",
        composition=True,
    ),
    EventTypeInfo(
        "flow.session.succeeded",
        "orchestration",
        "Flow session reached success",
        composition=True,
    ),
    EventTypeInfo(
        "flow.session.failed",
        "orchestration",
        "Flow session failed",
        composition=True,
    ),
    EventTypeInfo(
        "wizard.commit.succeeded",
        "wizard",
        "Wizard commit completed",
    ),
    EventTypeInfo(
        "wizard.commit.failed",
        "wizard",
        "Wizard commit failed",
    ),
    EventTypeInfo(
        "work.intent.enqueued",
        "work",
        "WorkIntent enqueued (run-when-able)",
    ),
    EventTypeInfo(
        "work.intent.succeeded",
        "work",
        "WorkIntent completed",
    ),
    EventTypeInfo(
        "work.intent.failed",
        "work",
        "WorkIntent failed",
    ),
    EventTypeInfo(
        "job.completed",
        "orchestration",
        "Job reached a terminal status",
        composition=True,
    ),
    EventTypeInfo(
        "job.status_changed",
        "orchestration",
        "Job status transition",
        composition=True,
    ),
    EventTypeInfo(
        "inbound.received",
        "inbound",
        "Inbound resource signal accepted (webhook/stream); WorkIntent may follow",
        composition=True,
    ),
)


def is_public_event_type(event_type: str) -> bool:
    return str(event_type or "") in PUBLIC_EVENT_TYPES


def filter_public_types(types: list[str] | None) -> list[str] | None:
    """None → all public; else intersection with public catalog."""
    if types is None:
        return None
    out = [t for t in types if is_public_event_type(str(t))]
    return out


def catalog_dict() -> dict[str, Any]:
    return {
        "version": 1,
        "public_types": sorted(PUBLIC_EVENT_TYPES),
        "composition_types": sorted(COMPOSITION_EVENT_TYPES),
        "events": [
            {
                "type": e.type,
                "category": e.category,
                "summary": e.summary,
                "composition": e.composition,
            }
            for e in _CATALOG
        ],
        "payload_policy": (
            "Prefer refs and ids (resource_ref, job_id, instance_id, action, hash). "
            "Do not put full resource documents on the bus or stream."
        ),
        "channels": {
            "live": "EventEngine (in-process)",
            "durable": "EventJournal (offsets)",
            "stream": "/ws/v1/events (0.42)",
            "http_catalog": "GET /v1/api/events/catalog",
            "http_journal": "GET /v1/api/events/journal",
        },
    }


__all__ = [
    "COMPOSITION_EVENT_TYPES",
    "PUBLIC_EVENT_TYPES",
    "EventTypeInfo",
    "catalog_dict",
    "filter_public_types",
    "is_public_event_type",
]
