"""
Blackboard — minimal shared key-value memory for the Orchestration Engine.

This is an independent implementation that lives inside the Orchestration
Engine package. It exists so that `palm/core/orchestration/` has **zero**
imports from the Behavior Tree Engine while still providing the exact same
public data-sharing contract that higher layers (and composition backends)
expect.

Design principles (identical to the canonical Behavior Tree Blackboard):
- All inter-component communication for a Job happens exclusively here.
- Callers are responsible for key hygiene.
- The implementation is deliberately minimal.
- Future extensions can be added without changing the get/set/has/clear contract.

Thread safety: Not provided. Higher layers manage concurrency.

This module (and the whole orchestration package) must remain completely
independent of wizards, CLI, persistence, domain models, and the Behavior
Tree Engine.
"""

from __future__ import annotations

from typing import Any


class Blackboard:
    """
    Shared memory used by Jobs, backends, and any code that needs to exchange
    data with a running unit of work.

    The public API is deliberately compatible with `palm.core.behavior_tree.Blackboard`
    so that `BehaviorTreeBackend` (and similar composition adapters) can share
    or migrate data with minimal friction.
    """

    def __init__(self) -> None:
        self._data: dict[str, Any] = {}

    def get(self, key: str, default: Any = None) -> Any:
        """Return the value for key, or default if absent."""
        return self._data.get(key, default)

    def set(self, key: str, value: Any) -> None:
        """Store value under key (overwrites if present)."""
        self._data[key] = value

    def has(self, key: str) -> bool:
        """Return True if key exists in the blackboard."""
        return key in self._data

    def clear(self) -> None:
        """Remove all entries. Use with extreme caution."""
        self._data.clear()

    def snapshot(self) -> dict[str, Any]:
        """Return a shallow copy of the entire blackboard (primarily for debugging/tests)."""
        return dict(self._data)

    def keys(self) -> list[str]:
        """Return list of all current keys (for inspection)."""
        return list(self._data.keys())

    def __repr__(self) -> str:
        return f"Blackboard(keys={len(self._data)})"
