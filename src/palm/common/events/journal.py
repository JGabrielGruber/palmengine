"""
Append-only event journal with named consumer offsets (0.38).

Kafka-*semantics* without cargo-cult: ordered log, at-least-once consumers,
optional latest-by-key compaction for ``resource.changed``. Not tiered document KV.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from palm.core.event import Event
    from palm.core.storage import StorageEngine

JOURNAL_SEQ = "palm:journal:seq"
JOURNAL_ENTRY_PREFIX = "palm:journal:entry:"
JOURNAL_OFFSET_PREFIX = "palm:journal:offset:"
JOURNAL_COMPACT_PREFIX = "palm:journal:compact:"  # latest offset per compact key


@dataclass
class JournalEntry:
    """One append-only journal record."""

    offset: int
    event_type: str
    payload: dict[str, Any] = field(default_factory=dict)
    context: dict[str, Any] | None = None
    timestamp: str = ""
    id: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "offset": self.offset,
            "event_type": self.event_type,
            "payload": dict(self.payload),
            "context": self.context,
            "timestamp": self.timestamp,
            "id": self.id,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> JournalEntry:
        return cls(
            offset=int(data.get("offset") or 0),
            event_type=str(data.get("event_type") or ""),
            payload=dict(data.get("payload") or {}),
            context=dict(data["context"]) if data.get("context") else None,
            timestamp=str(data.get("timestamp") or ""),
            id=str(data.get("id") or ""),
        )


class EventJournal:
    """
    Durable ordered log on StorageEngine.

    Offsets are 1-based sequence numbers. Consumers store last **committed**
    offset; ``read_after(offset)`` returns entries with offset > that value.
    """

    def __init__(self, storage: StorageEngine) -> None:
        self._storage = storage

    def append(
        self,
        event_type: str,
        payload: dict[str, Any] | None = None,
        *,
        context: dict[str, Any] | None = None,
        event_id: str | None = None,
        compact_key: str | None = None,
    ) -> int:
        """Append one entry; return its offset. Optional compact_key for latest-by-key."""
        seq = int(self._storage.get(JOURNAL_SEQ) or 0) + 1
        self._storage.set(JOURNAL_SEQ, seq)
        entry = JournalEntry(
            offset=seq,
            event_type=str(event_type),
            payload=dict(payload or {}),
            context=dict(context) if context else None,
            timestamp=datetime.now(UTC).isoformat(),
            id=event_id or uuid.uuid4().hex,
        )
        self._storage.set(f"{JOURNAL_ENTRY_PREFIX}{seq}", entry.to_dict())
        if compact_key:
            self._storage.set(f"{JOURNAL_COMPACT_PREFIX}{compact_key}", seq)
        return seq

    def append_event(self, event: Event, *, compact_key: str | None = None) -> int:
        ctx = event.context.to_dict() if event.context is not None else None
        return self.append(
            event.type,
            dict(event.payload),
            context=ctx,
            event_id=event.id,
            compact_key=compact_key,
        )

    def latest_offset(self) -> int:
        return int(self._storage.get(JOURNAL_SEQ) or 0)

    def get(self, offset: int) -> JournalEntry | None:
        raw = self._storage.get(f"{JOURNAL_ENTRY_PREFIX}{int(offset)}")
        if not isinstance(raw, dict):
            return None
        return JournalEntry.from_dict(raw)

    def read_after(
        self,
        offset: int = 0,
        *,
        limit: int = 100,
        event_types: frozenset[str] | None = None,
    ) -> list[JournalEntry]:
        """Return up to ``limit`` entries with offset > ``offset`` (ordered)."""
        latest = self.latest_offset()
        out: list[JournalEntry] = []
        pos = int(offset)
        while pos < latest and len(out) < limit:
            pos += 1
            entry = self.get(pos)
            if entry is None:
                continue
            if event_types is not None and entry.event_type not in event_types:
                continue
            out.append(entry)
        return out

    def get_consumer_offset(self, consumer: str) -> int:
        name = str(consumer or "").strip()
        if not name:
            return 0
        raw = self._storage.get(f"{JOURNAL_OFFSET_PREFIX}{name}")
        try:
            return int(raw or 0)
        except (TypeError, ValueError):
            return 0

    def commit_consumer_offset(self, consumer: str, offset: int) -> None:
        name = str(consumer or "").strip()
        if not name:
            raise ValueError("consumer name required")
        self._storage.set(f"{JOURNAL_OFFSET_PREFIX}{name}", int(offset))

    def consume(
        self,
        consumer: str,
        *,
        limit: int = 50,
        event_types: frozenset[str] | None = None,
        auto_commit: bool = True,
    ) -> list[JournalEntry]:
        """Read after consumer's offset; optionally advance offset to last entry."""
        start = self.get_consumer_offset(consumer)
        batch = self.read_after(start, limit=limit, event_types=event_types)
        if auto_commit and batch:
            self.commit_consumer_offset(consumer, batch[-1].offset)
        return batch

    def compacted_offset(self, compact_key: str) -> int | None:
        raw = self._storage.get(f"{JOURNAL_COMPACT_PREFIX}{compact_key}")
        if raw is None:
            return None
        try:
            return int(raw)
        except (TypeError, ValueError):
            return None

    def redrive(
        self,
        *,
        from_offset: int = 0,
        to_offset: int | None = None,
        event_types: frozenset[str] | None = None,
        limit: int = 500,
    ) -> list[JournalEntry]:
        """Read a range for replay (does not move consumer offsets)."""
        end = self.latest_offset() if to_offset is None else int(to_offset)
        out: list[JournalEntry] = []
        pos = max(0, int(from_offset))
        while pos < end and len(out) < limit:
            pos += 1
            entry = self.get(pos)
            if entry is None:
                continue
            if event_types is not None and entry.event_type not in event_types:
                continue
            out.append(entry)
        return out

    def status(self, *, consumers: list[str] | None = None) -> dict[str, Any]:
        """Observability snapshot for doctor / host recovery."""
        latest = self.latest_offset()
        consumer_rows: dict[str, Any] = {}
        for name in consumers or []:
            off = self.get_consumer_offset(name)
            consumer_rows[name] = {
                "offset": off,
                "lag": max(0, latest - off),
            }
        return {
            "latest_offset": latest,
            "consumers": consumer_rows,
        }


def compact_key_for_resource_changed(payload: dict[str, Any]) -> str | None:
    """Build compact key for resource.changed (latest-by-resource)."""
    ref = payload.get("resource_ref") or payload.get("definition_name")
    rid = payload.get("resource_id") or ""
    if not ref:
        return None
    return f"resource.changed:{ref}:{rid}"


__all__ = [
    "JOURNAL_COMPACT_PREFIX",
    "JOURNAL_ENTRY_PREFIX",
    "JOURNAL_OFFSET_PREFIX",
    "JOURNAL_SEQ",
    "EventJournal",
    "JournalEntry",
    "compact_key_for_resource_changed",
]
