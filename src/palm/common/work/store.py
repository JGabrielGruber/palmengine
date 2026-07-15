"""Durable WorkIntent store (StorageEngine), coalesce-aware."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from palm.core.work import WorkIntent

if TYPE_CHECKING:
    from palm.core.storage import StorageEngine

WORK_PENDING_INDEX = "palm:work:pending_index"
WORK_ENTRY_PREFIX = "palm:work:entry:"
WORK_COALESCE_PREFIX = "palm:work:coalesce:"


class WorkIntentStore:
    """Append / claim / ack work intents (run-when-able queue)."""

    def __init__(self, storage: StorageEngine) -> None:
        self._storage = storage

    def enqueue(self, intent: WorkIntent) -> str:
        data = intent.to_dict()
        data["status"] = "pending"
        if intent.coalesce_key:
            existing_id = self._storage.get(
                f"{WORK_COALESCE_PREFIX}{intent.coalesce_key}"
            )
            if isinstance(existing_id, str) and existing_id:
                self._remove_pending(existing_id)
        self._storage.set(f"{WORK_ENTRY_PREFIX}{intent.id}", data)
        index = self._load_index()
        if intent.id not in index:
            index.append(intent.id)
            self._storage.set(WORK_PENDING_INDEX, index)
        if intent.coalesce_key:
            self._storage.set(
                f"{WORK_COALESCE_PREFIX}{intent.coalesce_key}", intent.id
            )
        return intent.id

    def claim_due(
        self, *, limit: int = 10, now: datetime | None = None
    ) -> list[WorkIntent]:
        claimed: list[WorkIntent] = []
        for entry_id in list(self._load_index()):
            if len(claimed) >= limit:
                break
            raw = self._storage.get(f"{WORK_ENTRY_PREFIX}{entry_id}")
            if not isinstance(raw, dict):
                self._remove_pending(entry_id)
                continue
            intent = WorkIntent.from_dict(raw)
            if intent.status != "pending":
                continue
            if not intent.is_due(now=now):
                continue
            updated = WorkIntent.from_dict(
                {**intent.to_dict(), "status": "claimed"}
            )
            self._storage.set(f"{WORK_ENTRY_PREFIX}{entry_id}", updated.to_dict())
            claimed.append(updated)
        return claimed

    def ack(self, intent_id: str) -> None:
        key = f"{WORK_ENTRY_PREFIX}{intent_id}"
        raw = self._storage.get(key)
        if isinstance(raw, dict):
            raw = {**raw, "status": "done"}
            self._storage.set(key, raw)
            ck = raw.get("coalesce_key")
            if ck:
                cur = self._storage.get(f"{WORK_COALESCE_PREFIX}{ck}")
                if cur == intent_id:
                    self._storage.delete(f"{WORK_COALESCE_PREFIX}{ck}")
        self._remove_pending(intent_id)

    def fail(self, intent_id: str, error: str) -> None:
        key = f"{WORK_ENTRY_PREFIX}{intent_id}"
        raw = self._storage.get(key)
        if not isinstance(raw, dict):
            self._remove_pending(intent_id)
            return
        attempts = int(raw.get("attempt") or 0) + 1
        raw["attempt"] = attempts
        raw["last_error"] = error
        if attempts >= 5:
            raw["status"] = "failed"
            self._remove_pending(intent_id)
        else:
            raw["status"] = "pending"
        self._storage.set(key, raw)

    def pending_count(self) -> int:
        return len(self._load_index())

    def list_pending(self, *, limit: int = 100) -> list[WorkIntent]:
        out: list[WorkIntent] = []
        for entry_id in self._load_index()[:limit]:
            raw = self._storage.get(f"{WORK_ENTRY_PREFIX}{entry_id}")
            if isinstance(raw, dict):
                out.append(WorkIntent.from_dict(raw))
        return out

    def _load_index(self) -> list[str]:
        raw = self._storage.get(WORK_PENDING_INDEX)
        if not isinstance(raw, list):
            return []
        return [str(i) for i in raw]

    def _remove_pending(self, intent_id: str) -> None:
        index = self._load_index()
        if intent_id in index:
            index.remove(intent_id)
            self._storage.set(WORK_PENDING_INDEX, index)


__all__ = [
    "WORK_COALESCE_PREFIX",
    "WORK_ENTRY_PREFIX",
    "WORK_PENDING_INDEX",
    "WorkIntentStore",
]
