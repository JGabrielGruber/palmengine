"""Chat continuity policy hooks (auto-start / intro) — migrate off WS here over time.

WS still owns the live implementation in 0.32; these constants document the contract
and give a single import path for 0.33.2+.
"""

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
    "wants_auto_continue_intro",
    "wants_auto_start",
]
