"""Chat profile — Portal / WS humans: input schema, quiet actions, continuity."""

from __future__ import annotations

from typing import Any

from palm.services.assist.profiles.actions_chat import (
    filter_chat_noise_actions,
    rewrite_actions_for_chat,
)
from palm.services.assist.profiles.base import AssistProfile, RenderOptions
from palm.services.assist.profiles.continuity import apply_chat_continuity

# Back-compat alias used by older imports
filter_chat_actions = filter_chat_noise_actions


def chat_render_options(**overrides: Any) -> RenderOptions:
    return RenderOptions.for_chat(**overrides)


def apply_chat_action_policy(payload: dict[str, Any]) -> dict[str, Any]:
    """Mutate a shaped turn for chat: rewrite + filter actions when present."""
    return rewrite_actions_for_chat(payload)


PROFILE = AssistProfile.CHAT

__all__ = [
    "PROFILE",
    "apply_chat_action_policy",
    "apply_chat_continuity",
    "chat_render_options",
    "filter_chat_actions",
    "filter_chat_noise_actions",
    "rewrite_actions_for_chat",
]
