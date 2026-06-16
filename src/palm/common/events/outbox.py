"""
Transactional outbox — durable event queue backed by StorageEngine.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from collections.abc import Callable
from typing import Any

from palm.core.event import Event, EventContext, EventEngine
from palm.core.storage import StorageEngine

OUTBOX_PENDING_INDEX = "palm:outbox:pending_index"
OUTBOX_ENTRY_PREFIX = "palm:outbox:entry:"


@dataclass
class OutboxEntry:
    """Serialized event awaiting reliable delivery."""

    id: str
    event_type: str
    payload: dict[str, Any] = field(default_factory=dict)
    context: dict[str, Any] | None = None
    timestamp: str = ""
    status: str = "pending"
    attempts: int = 0
    last_error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "event_type": self.event_type,
            "payload": self.payload,
            "context": self.context,
            "timestamp": self.timestamp,
            "status": self.status,
            "attempts": self.attempts,
            "last_error": self.last_error,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> OutboxEntry:
        return cls(
            id=str(data["id"]),
            event_type=str(data["event_type"]),
            payload=dict(data.get("payload") or {}),
            context=dict(data["context"]) if data.get("context") else None,
            timestamp=str(data.get("timestamp") or ""),
            status=str(data.get("status") or "pending"),
            attempts=int(data.get("attempts") or 0),
            last_error=data.get("last_error"),
        )

    def to_event(self) -> Event:
        ts = datetime.fromisoformat(self.timestamp) if self.timestamp else datetime.now(UTC)
        return Event(
            id=self.id,
            type=self.event_type,
            payload=dict(self.payload),
            timestamp=ts,
            context=EventContext.from_dict(self.context),
        )

    @classmethod
    def from_event(cls, event: Event) -> OutboxEntry:
        return cls(
            id=event.id,
            event_type=event.type,
            payload=dict(event.payload),
            context=event.context.to_dict() if event.context is not None else None,
            timestamp=event.timestamp.isoformat(),
            status="pending",
        )


class OutboxStore:
    """Persist outbox entries through a :class:`~palm.core.storage.StorageEngine`."""

    def __init__(self, storage: StorageEngine) -> None:
        self._storage = storage

    def enqueue(self, event: Event) -> str:
        entry = OutboxEntry.from_event(event)
        self._storage.set(f"{OUTBOX_ENTRY_PREFIX}{entry.id}", entry.to_dict())
        index = self._load_index()
        if entry.id not in index:
            index.append(entry.id)
            self._storage.set(OUTBOX_PENDING_INDEX, index)
        return entry.id

    def list_pending(self, *, limit: int = 100) -> list[OutboxEntry]:
        index = self._load_index()
        entries: list[OutboxEntry] = []
        for entry_id in index[:limit]:
            raw = self._storage.get(f"{OUTBOX_ENTRY_PREFIX}{entry_id}")
            if not isinstance(raw, dict):
                continue
            entry = OutboxEntry.from_dict(raw)
            if entry.status == "pending":
                entries.append(entry)
        return entries

    def mark_published(self, entry_id: str) -> None:
        key = f"{OUTBOX_ENTRY_PREFIX}{entry_id}"
        raw = self._storage.get(key)
        if not isinstance(raw, dict):
            return
        entry = OutboxEntry.from_dict(raw)
        entry.status = "published"
        self._storage.set(key, entry.to_dict())
        index = self._load_index()
        if entry_id in index:
            index.remove(entry_id)
            self._storage.set(OUTBOX_PENDING_INDEX, index)

    def mark_failed(self, entry_id: str, error: str) -> None:
        key = f"{OUTBOX_ENTRY_PREFIX}{entry_id}"
        raw = self._storage.get(key)
        if not isinstance(raw, dict):
            return
        entry = OutboxEntry.from_dict(raw)
        entry.attempts += 1
        entry.last_error = error
        if entry.attempts >= 5:
            entry.status = "failed"
            index = self._load_index()
            if entry_id in index:
                index.remove(entry_id)
                self._storage.set(OUTBOX_PENDING_INDEX, index)
        self._storage.set(key, entry.to_dict())

    def pending_count(self) -> int:
        return len(self._load_index())

    def _load_index(self) -> list[str]:
        raw = self._storage.get(OUTBOX_PENDING_INDEX)
        if not isinstance(raw, list):
            return []
        return [str(item) for item in raw]


class OutboxProcessor:
    """
    Drain pending outbox entries.

    By default entries are marked published without re-dispatching handlers
    (live publish already ran). Set ``replay_handlers=True`` for recovery.
    """

    def __init__(self, store: OutboxStore, event_engine: EventEngine) -> None:
        self._store = store
        self._event_engine = event_engine

    def process_batch(
        self,
        *,
        limit: int = 50,
        replay_handlers: bool = False,
        on_before_publish: Callable[[Event], None] | None = None,
    ) -> int:
        processed = 0
        for entry in self._store.list_pending(limit=limit):
            try:
                event = entry.to_event()
                if on_before_publish is not None:
                    on_before_publish(event)
                if replay_handlers:
                    self._event_engine.publish(event, source="outbox")
                self._store.mark_published(entry.id)
                processed += 1
            except Exception as exc:
                self._store.mark_failed(entry.id, str(exc))
        return processed

    def recover_pending(self, *, replay_handlers: bool = True) -> int:
        """Process all pending entries — useful on startup."""
        total = 0
        while True:
            count = self.process_batch(limit=50, replay_handlers=replay_handlers)
            if count == 0:
                break
            total += count
        return total