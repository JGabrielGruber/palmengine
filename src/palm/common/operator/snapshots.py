"""Snapshot diff helpers for operator debugging."""

from __future__ import annotations

from typing import Any


def diff_snapshot_states(
    before: dict[str, Any],
    after: dict[str, Any],
    *,
    ignore_prefixes: tuple[str, ...] = ("__bt_", "__palm:", "__wizard__"),
) -> dict[str, Any]:
    """Compare two blackboard snapshot dicts and return key-level changes."""
    before_state = _state_dict(before)
    after_state = _state_dict(after)

    added: list[str] = []
    removed: list[str] = []
    changed: list[dict[str, Any]] = []

    all_keys = sorted(set(before_state) | set(after_state))
    for key in all_keys:
        if any(key.startswith(prefix) for prefix in ignore_prefixes):
            continue
        in_before = key in before_state
        in_after = key in after_state
        if in_before and not in_after:
            removed.append(key)
            continue
        if in_after and not in_before:
            added.append(key)
            continue
        old = before_state[key]
        new = after_state[key]
        if old != new:
            changed.append(
                {
                    "key": key,
                    "before_preview": _preview(old),
                    "after_preview": _preview(new),
                }
            )

    return {
        "added_keys": added,
        "removed_keys": removed,
        "changed": changed,
        "change_count": len(added) + len(removed) + len(changed),
    }


def _state_dict(snapshot: dict[str, Any]) -> dict[str, Any]:
    raw = snapshot.get("state_snapshot")
    if isinstance(raw, dict):
        return dict(raw)
    return {}


def _preview(value: Any, *, limit: int = 200) -> Any:
    if isinstance(value, str):
        if len(value) <= limit:
            return value
        return value[:limit] + "…"
    rendered = str(value)
    if len(rendered) <= limit:
        return value
    return rendered[:limit] + "…"


__all__ = ["diff_snapshot_states"]
