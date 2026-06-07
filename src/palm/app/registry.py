"""
Runtime registry — named runtime handles managed by :class:`~palm.app.app.PalmApp`.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Literal

if TYPE_CHECKING:
    from palm.runtimes.base import BaseRuntime

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
    """In-memory map of named runtimes."""

    def __init__(self) -> None:
        self._entries: dict[str, RuntimeHandle] = {}

    def __len__(self) -> int:
        return len(self._entries)

    def __contains__(self, name: str) -> bool:
        return name in self._entries

    def names(self) -> list[str]:
        return sorted(self._entries)

    def register(self, handle: RuntimeHandle) -> RuntimeHandle:
        if handle.name in self._entries:
            raise ValueError(f"Runtime {handle.name!r} is already registered")
        self._entries[handle.name] = handle
        return handle

    def get(self, name: str) -> RuntimeHandle:
        try:
            return self._entries[name]
        except KeyError as exc:
            available = ", ".join(self.names()) or "(none)"
            raise KeyError(f"Unknown runtime {name!r}. Registered: {available}") from exc

    def items(self) -> list[RuntimeHandle]:
        return [self._entries[name] for name in self.names()]

    def clear(self) -> None:
        self._entries.clear()