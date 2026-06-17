"""Optional TTL caches for resource definition resolution and read results."""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class ResourceCacheConfig:
    """Configure optional ResourceEngine caches (all off by default except definitions)."""

    cache_definitions: bool = True
    cache_results: bool = False
    ttl_seconds: float = 60.0
    max_entries: int = 256
    cacheable_actions: frozenset[str] = field(default_factory=lambda: frozenset({"fetch"}))


class TtlCache:
    """Simple in-memory TTL cache with a max entry bound."""

    def __init__(self, *, max_entries: int = 256, ttl_seconds: float = 60.0) -> None:
        self._max_entries = max(1, max_entries)
        self._ttl_seconds = max(0.0, ttl_seconds)
        self._entries: dict[str, tuple[float, Any]] = {}

    def get(self, key: str) -> Any | None:
        entry = self._entries.get(key)
        if entry is None:
            return None
        expires_at, value = entry
        if time.monotonic() > expires_at:
            self._entries.pop(key, None)
            return None
        return value

    def set(self, key: str, value: Any) -> None:
        if len(self._entries) >= self._max_entries:
            self._evict_oldest()
        expires_at = time.monotonic() + self._ttl_seconds
        self._entries[key] = (expires_at, value)

    def clear(self) -> None:
        self._entries.clear()

    def _evict_oldest(self) -> None:
        if not self._entries:
            return
        oldest_key = min(self._entries, key=lambda item: self._entries[item][0])
        self._entries.pop(oldest_key, None)


def definition_cache_key(resource_ref: str) -> str:
    return f"def:{resource_ref}"


def result_cache_key(
    *,
    provider: str,
    action: str,
    resource_ref: str | None,
    resource_id: str | None,
    params: dict[str, Any],
) -> str:
    payload = {
        "provider": provider,
        "action": action,
        "resource_ref": resource_ref,
        "resource_id": resource_id,
        "params": params,
    }
    return f"result:{json.dumps(payload, sort_keys=True, default=str)}"