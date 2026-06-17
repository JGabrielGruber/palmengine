"""Resource compensation helpers — mutating invoke tracking and undo keys."""

from __future__ import annotations

from typing import Any

READ_ONLY_ACTIONS = frozenset({"fetch", "health", "describe"})


def is_mutating_action(action: str | None) -> bool:
    """Return whether an invoke action may require undo on failure or backtrack."""
    if not action:
        return False
    return action.strip().lower() not in READ_ONLY_ACTIONS


def compensation_key(
    resource_ref: str | None,
    *,
    metadata: dict[str, Any] | None = None,
) -> str | None:
    """Resolve the registry key for a resource undo handler."""
    if metadata:
        explicit = metadata.get("compensation_key")
        if explicit:
            return str(explicit)
    return resource_ref


def track_resource_invocation(
    invocations: list[dict[str, Any]],
    *,
    resource_ref: str,
    action: str,
    provider: str | None = None,
    resource_id: str | None = None,
    step_slug: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    """Append a mutating resource record for commit-failure compensation."""
    if not is_mutating_action(action):
        return invocations
    key = compensation_key(resource_ref, metadata=metadata)
    if not key:
        return invocations
    record = {
        "resource_ref": resource_ref,
        "compensation_key": key,
        "action": action,
        "provider": provider,
        "resource_id": resource_id,
        "step_slug": step_slug,
    }
    updated = list(invocations)
    updated.append(record)
    return updated


def resource_refs_for_compensation(invocations: list[dict[str, Any]]) -> list[str]:
    """Distinct compensation keys from tracked mutating invocations."""
    keys: list[str] = []
    seen: set[str] = set()
    for entry in invocations:
        if not isinstance(entry, dict):
            continue
        key = entry.get("compensation_key") or entry.get("resource_ref")
        if not key or key in seen:
            continue
        seen.add(str(key))
        keys.append(str(key))
    return keys
