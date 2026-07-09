"""Chat profile — Portal / WS humans: input schema, quiet actions."""

from __future__ import annotations

from typing import Any

from palm.services.assist.profiles.base import AssistProfile, RenderOptions

# Agent chrome to hide in floating chat (also filtered client-side).
_CHAT_DROP_LABELS = frozenset(
    {
        "inspect session",
        "send answer",
        "resume session",
        "open child session",
    }
)


def chat_render_options(**overrides: Any) -> RenderOptions:
    return RenderOptions.for_chat(**overrides)


def filter_chat_actions(actions: list[dict[str, Any]] | None) -> list[dict[str, Any]]:
    """Keep human-primary CTAs; drop operator-tool noise."""
    if not actions:
        return []
    out: list[dict[str, Any]] = []
    for action in actions:
        if not isinstance(action, dict):
            continue
        label = str(action.get("label") or "").strip().lower()
        if label in _CHAT_DROP_LABELS:
            continue
        # Drop bare "Send answer" path duplicates; keep Start / Hand off / Cancel / Go back
        out.append(dict(action))
    return out


def apply_chat_action_policy(payload: dict[str, Any]) -> dict[str, Any]:
    """Mutate a shaped turn for chat: filter actions when present."""
    actions = payload.get("actions")
    if isinstance(actions, list):
        filtered = filter_chat_actions(actions)
        if filtered:
            payload["actions"] = filtered
        else:
            payload.pop("actions", None)
    return payload


PROFILE = AssistProfile.CHAT

__all__ = [
    "PROFILE",
    "apply_chat_action_policy",
    "chat_render_options",
    "filter_chat_actions",
]
