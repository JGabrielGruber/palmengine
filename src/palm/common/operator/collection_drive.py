"""Wizard collection step driving — one-shot menu add and compound flows."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from typing import Any

MENU_ADD_LABEL = "Add a new item"
COLLECTION_ADD_ONE_SHOT = "__collection_add_one_shot__"


def drive_collection_add(
    provide_input: Callable[[Any], dict[str, Any]],
    *,
    value: Any,
    wizard_view: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Apply menu-phase add then field value in one call (weak-LLM ergonomics)."""
    view = dict(wizard_view or {})
    prompt = view.get("prompt") or {}
    phase = prompt.get("collection_phase") or view.get("collection_phase")

    if phase in (None, "menu"):
        view = provide_input(MENU_ADD_LABEL)
        prompt = view.get("prompt") or {}
        phase = prompt.get("collection_phase")

    if phase == "field":
        raw = value if isinstance(value, str) else str(value)
        return provide_input(raw)

    raise ValueError(
        "collection add one-shot expected field phase after menu; "
        f"got collection_phase={phase!r}"
    )


__all__ = ["COLLECTION_ADD_ONE_SHOT", "MENU_ADD_LABEL", "drive_collection_add"]