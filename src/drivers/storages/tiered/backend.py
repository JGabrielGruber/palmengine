"""Tiered storage — a hot map on this instance, write-through to a cold backend."""

from __future__ import annotations

import threading
from collections import OrderedDict
from typing import Any

from palm.core.storage import BaseBackend


class TieredBackend(BaseBackend):
    """Storage that keeps a bounded hot map and writes every change to ``cold``.

    The hot map belongs to this instance. ``close`` drops that map.
    The caller owns ``cold`` and closes it.
    """

    def __init__(
        self,
        *,
        name: str = "tiered",
        cold: BaseBackend,
        hot_max_keys: int = 500,
    ) -> None:
        super().__init__(name=name)
        if hot_max_keys < 1:
            raise ValueError("hot_max_keys must be >= 1")
        self._cold = cold
        self._hot_max_keys = hot_max_keys
        self._hot: dict[str, Any] = {}
        self._lru: OrderedDict[str, None] = OrderedDict()
        self._lock = threading.RLock()

    @property
    def cold(self) -> BaseBackend:
        """The backend that keeps every written key."""
        return self._cold

    def open(self) -> None:
        if self._is_open:
            return
        if not self._cold.is_open:
            self._cold.open()
        self._is_open = True

    def get(self, key: str) -> Any | None:
        self.ensure_open()
        with self._lock:
            if key in self._hot:
                self._touch(key)
                return self._hot[key]
        value = self._cold.get(key)
        if value is None:
            return None
        self._remember(key, value)
        return value

    def set(self, key: str, value: Any) -> None:
        self.ensure_open()
        self._cold.set(key, value)
        self._remember(key, value)

    def delete(self, key: str) -> None:
        self.ensure_open()
        with self._lock:
            self._hot.pop(key, None)
            self._lru.pop(key, None)
        self._cold.delete(key)

    def close(self) -> None:
        if not self._is_open:
            return
        with self._lock:
            self._hot.clear()
            self._lru.clear()
        self._is_open = False

    def keys_with_prefix(self, prefix: str) -> list[str]:
        self.ensure_open()
        with self._lock:
            hot = {key for key in self._hot if key.startswith(prefix)}
        cold = set(self._cold.keys_with_prefix(prefix))
        return sorted(hot | cold)

    def _remember(self, key: str, value: Any) -> None:
        with self._lock:
            self._hot[key] = value
            self._touch(key)
            while len(self._lru) > self._hot_max_keys:
                evicted, _ = self._lru.popitem(last=False)
                self._hot.pop(evicted, None)

    def _touch(self, key: str) -> None:
        self._lru.pop(key, None)
        self._lru[key] = None


__all__ = ["TieredBackend"]
