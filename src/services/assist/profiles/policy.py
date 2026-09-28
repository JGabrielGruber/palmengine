"""Chat continuity flags and auto-start intent sets (profile contract)."""

from __future__ import annotations

from typing import Any

# Demo flow intents that skip summary and auto-start on chat complete
CHAT_AUTO_START_INTENTS = frozenset(
    {
        "todo-builder",
        "compositional-parent",
        "coconut-npc",
    }
)

# Operator-entry design intents → design-entry scenario (0.34.1)
CHAT_DESIGN_AUTO_START_INTENTS = frozenset(
    {
        "create-flow",
        "improve-flow",
        "propose-resource",
    }
)

CHAT_DESIGN_SCENARIO_ID = "design-entry"


def wants_auto_start(params: dict[str, Any] | None, *, default: bool = True) -> bool:
    if not params:
        return default
    if "auto_start" not in params:
        return default
    raw = params.get("auto_start")
    if raw is False or raw == 0:
        return False
    if isinstance(raw, str) and raw.strip().lower() in {"0", "false", "no", "off"}:
        return False
    return True


def wants_auto_continue_intro(params: dict[str, Any] | None, *, default: bool = True) -> bool:
    if not params:
        return default
    if "auto_continue_intro" not in params:
        return default
    raw = params.get("auto_continue_intro")
    if raw is False or raw == 0:
        return False
    if isinstance(raw, str) and raw.strip().lower() in {"0", "false", "no", "off"}:
        return False
    return True


__all__ = [
    "CHAT_AUTO_START_INTENTS",
    "CHAT_DESIGN_AUTO_START_INTENTS",
    "CHAT_DESIGN_SCENARIO_ID",
    "wants_auto_continue_intro",
    "wants_auto_start",
]
