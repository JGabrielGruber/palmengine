"""
Shared blackboard for behavior tree execution.

All inter-node data flows through the blackboard. Nodes should use disciplined
key naming (prefixes, namespaces) to avoid collisions.
"""

from __future__ import annotations

from typing import Any


class Blackboard:
    """Key-value store used by all nodes in a behavior tree."""

    def __init__(self, initial: dict[str, Any] | None = None) -> None:
        self._data: dict[str, Any] = dict(initial) if initial else {}

    def get(self, key: str, default: Any = None) -> Any:
        return self._data.get(key, default)

    def set(self, key: str, value: Any) -> None:
        self._data[key] = value

    def has(self, key: str) -> bool:
        return key in self._data

    def delete(self, key: str) -> None:
        self._data.pop(key, None)

    def clear(self) -> None:
        self._data.clear()

    def snapshot(self) -> dict[str, Any]:
        return dict(self._data)

    def keys(self) -> list[str]:
        return list(self._data.keys())

    def __repr__(self) -> str:
        return f"Blackboard(keys={len(self._data)})"