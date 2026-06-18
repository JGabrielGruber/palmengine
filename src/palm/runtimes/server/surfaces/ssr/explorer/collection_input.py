"""Collection step input resolution for Explorer forms."""

from __future__ import annotations

from typing import Any, Mapping


def resolve_wizard_form_input(
    form_data: Mapping[str, Any],
    wizard: Mapping[str, Any],
) -> str | tuple[str, ...]:
    """Map Explorer collection UI posts to wizard ``provide_input`` values."""
    action = str(form_data.get("collection_action") or "").strip().lower()
    if action == "add":
        return "Add a new item"
    if action == "done":
        return _done_choice(wizard)
    if action == "cancel":
        return "cancel"
    if action == "edit" and form_data.get("item_index") is not None:
        return ("__compound_edit__", int(form_data["item_index"]))
    if action == "remove" and form_data.get("item_index") is not None:
        return ("__compound_remove__", int(form_data["item_index"]))
    if action == "confirm_remove":
        return str(form_data.get("value", "yes"))
    if action == "select_item" and form_data.get("item_index") is not None:
        return str(int(form_data["item_index"]) + 1)

    raw = form_data.get("value", "")
    return raw if raw != "" else ""


def _done_choice(wizard: Mapping[str, Any]) -> str:
    prompt = wizard.get("prompt") or {}
    choices = prompt.get("choices") or []
    for choice in choices:
        text = str(choice)
        if text.startswith("Continue to summary"):
            return text
    return "Continue to summary"