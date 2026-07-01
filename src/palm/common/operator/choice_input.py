"""
Menu choice resolution for operator input — generic slug/label/number matching.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any


_ACTION_KEYWORDS: dict[str, tuple[str, ...]] = {
    "add": ("add a new item", "add"),
    "edit": ("edit an item", "edit"),
    "remove": ("remove an item", "remove"),
    "done": ("continue to summary", "done"),
    "continue": ("continue to summary", "continue"),
}


def resolve_collection_action_choice(action: str, choices: Sequence[str]) -> str | None:
    """Map short action tokens (add, done, edit) to a menu choice label."""
    if not choices:
        return None
    normalized = str(action or "").strip().lower()
    keywords = _ACTION_KEYWORDS.get(normalized)
    if keywords:
        matches = [
            choice
            for choice in choices
            if any(keyword in str(choice).lower() for keyword in keywords)
        ]
        if len(matches) == 1:
            return str(matches[0])
    return resolve_menu_choice(action, choices)


def resolve_menu_choice(value: Any, choices: Sequence[str]) -> str | None:
    """Resolve raw operator input to a canonical menu choice, if possible."""
    if not choices or not isinstance(value, str):
        return None

    text = value.strip()
    if not text:
        return None
    if text in choices:
        return text

    lowered = text.lower()
    case_insensitive = [choice for choice in choices if choice.lower() == lowered]
    if len(case_insensitive) == 1:
        return case_insensitive[0]

    if text.isdigit():
        index = int(text)
        if 1 <= index <= len(choices):
            return choices[index - 1]

    prefix_matches = [choice for choice in choices if choice.lower().startswith(lowered)]
    if len(prefix_matches) == 1:
        return prefix_matches[0]

    substring_matches = [choice for choice in choices if lowered in choice.lower()]
    if len(substring_matches) == 1:
        return substring_matches[0]

    return None


__all__ = ["resolve_collection_action_choice", "resolve_menu_choice"]
