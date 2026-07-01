"""
Wizard collection step input resolution — map UI/MCP actions to provide_input values.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from palm.common.operator.choice_input import resolve_collection_action_choice


def resolve_wizard_form_input(
    form_data: Mapping[str, Any],
    wizard: Mapping[str, Any],
) -> str | tuple[str, int]:
    """Map Explorer collection form posts to wizard ``provide_input`` values."""
    action = str(form_data.get("collection_action") or "").strip().lower()
    item_index = form_data.get("item_index")
    parsed_index = int(item_index) if item_index is not None else None
    return resolve_wizard_collection_action(
        action,
        item_index=parsed_index,
        value=form_data.get("value"),
        wizard_view=wizard,
    )


def resolve_wizard_collection_action(
    action: str,
    *,
    item_index: int | None = None,
    value: Any = None,
    wizard_view: Mapping[str, Any] | None = None,
) -> str | tuple[str, int]:
    """Map a collection action name to a wizard input value."""
    normalized = str(action or "").strip().lower()
    wizard = wizard_view or {}
    prompt = wizard.get("prompt") or {}
    choices = prompt.get("choices") or []
    if choices and normalized in {"add", "edit", "remove", "done", "continue"}:
        matched = resolve_collection_action_choice(
            normalized,
            [str(choice) for choice in choices],
        )
        if matched is not None and normalized != "add":
            if normalized == "edit" and item_index is not None:
                return ("__compound_edit__", item_index)
            if normalized == "remove" and item_index is not None:
                return ("__compound_remove__", item_index)
            return matched

    if normalized == "add":
        if value is not None:
            raise ValueError(
                "'add' is a menu-phase collection action; "
                "provide field values via palm_flows_session_input(input=…)"
            )
        return "Add a new item"
    if normalized == "done":
        return _done_choice(wizard)
    if normalized == "cancel":
        return "cancel"
    if normalized == "edit" and item_index is not None:
        return ("__compound_edit__", item_index)
    if normalized == "remove" and item_index is not None:
        return ("__compound_remove__", item_index)
    if normalized == "confirm_remove":
        return str(value if value is not None else "yes")
    if normalized == "select_item" and item_index is not None:
        return str(item_index + 1)

    if value is not None and value != "":
        return value if isinstance(value, str) else str(value)
    return ""


def _done_choice(wizard: Mapping[str, Any]) -> str:
    prompt = wizard.get("prompt") or {}
    choices = prompt.get("choices") or []
    if choices:
        matched = resolve_collection_action_choice("done", [str(choice) for choice in choices])
        if matched is not None:
            return matched
    for choice in choices:
        text = str(choice)
        if text.startswith("Continue to summary"):
            return text
    return "Continue to summary"


__all__ = ["resolve_wizard_collection_action", "resolve_wizard_form_input"]
