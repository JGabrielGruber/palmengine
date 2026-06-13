"""
Runtime registry — named runtime handles managed by :class:`~palm.app.app.PalmApp`.
"""

from __future__ import annotations

import threading
from dataclasses import dataclass
from typing import TYPE_CHECKING, Literal

if TYPE_CHECKING:
    from palm.common.runtimes.base import BaseRuntime

RuntimeKind = Literal["embedded", "daemon", "server"]


@dataclass
class RuntimeHandle:
    """A named runtime instance registered on the application."""

    name: str
    kind: RuntimeKind
    runtime: BaseRuntime

    @property
    def is_started(self) -> bool:
        return self.runtime.is_started


class RuntimeRegistry:
    """Thread-safe in-memory map of named runtimes."""

    def __init__(self) -> None:
        self._entries: dict[str, RuntimeHandle] = {}
        self._lock = threading.RLock()

    def __len__(self) -> int:
        with self._lock:
            return len(self._entries)

    def __contains__(self, name: str) -> bool:
        with self._lock:
            return name in self._entries

    def names(self) -> list[str]:
        with self._lock:
            return sorted(self._entries)

    def register(self, handle: RuntimeHandle) -> RuntimeHandle:
        with self._lock:
            if handle.name in self._entries:
                raise ValueError(f"Runtime {handle.name!r} is already registered")
            self._entries[handle.name] = handle
            return handle

    def get(self, name: str) -> RuntimeHandle:
        with self._lock:
            try:
                return self._entries[name]
            except KeyError as exc:
                available = ", ".join(sorted(self._entries)) or "(none)"
                raise KeyError(f"Unknown runtime {name!r}. Registered: {available}") from exc

    def items(self) -> list[RuntimeHandle]:
        with self._lock:
            return [self._entries[name] for name in sorted(self._entries)]

    def clear(self) -> None:
        with self._lock:
            self._entries.clear()
