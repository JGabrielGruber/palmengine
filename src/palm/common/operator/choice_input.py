"""
Menu choice resolution for operator input — generic slug/label/number matching.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any


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


__all__ = ["resolve_menu_choice"]