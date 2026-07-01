"""Wizard collection compound edit — menu select + sequential field inputs."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from typing import Any

EDIT_MENU_LABEL = "Edit an item"


def drive_collection_edit(
    provide_input: Callable[[Any], dict[str, Any]],
    *,
    item_index: int,
    fields: Mapping[str, Any],
    wizard_view: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Drive edit menu → item select → field values from ``fields``."""
    from palm.common.operator.input_coercion import coerce_collection_field_input

    view = dict(wizard_view or {})
    merged = _merge_edit_fields(view, item_index, fields)
    view = provide_input(EDIT_MENU_LABEL)
    view = provide_input(str(item_index + 1))

    slugs = _collection_field_slugs(view) or list(merged.keys())
    for slug in slugs:
        if slug not in merged:
            if _field_is_optional(view, slug):
                merged[slug] = ""
            else:
                raise ValueError(f"edit missing value for field {slug!r}")
        coerced = coerce_collection_field_input(merged[slug], view)
        view = provide_input(coerced)
    return view


def _merge_edit_fields(
    wizard_view: Mapping[str, Any],
    item_index: int,
    fields: Mapping[str, Any],
) -> dict[str, Any]:
    combined = dict(_collection_item_at(wizard_view, item_index))
    combined.update(dict(fields))
    return combined


def _collection_item_at(wizard_view: Mapping[str, Any], item_index: int) -> dict[str, Any]:
    prompt = wizard_view.get("prompt") or {}
    collection_key = prompt.get("collection_key")
    answers = wizard_view.get("answers_preview") or wizard_view.get("answers") or {}
    if isinstance(collection_key, str):
        items = answers.get(collection_key) or []
        if 0 <= item_index < len(items) and isinstance(items[item_index], dict):
            return dict(items[item_index])
    for value in answers.values():
        if isinstance(value, list) and 0 <= item_index < len(value):
            entry = value[item_index]
            if isinstance(entry, dict):
                return dict(entry)
    return {}


def _field_is_optional(wizard_view: Mapping[str, Any], slug: str) -> bool:
    prompt = wizard_view.get("prompt") or {}
    for field in prompt.get("item_fields") or []:
        if isinstance(field, dict) and str(field.get("slug")) == slug:
            return not bool(field.get("required", True))
    return False


def _collection_field_slugs(wizard_view: Mapping[str, Any]) -> list[str]:
    prompt = wizard_view.get("prompt") or {}
    item_fields = prompt.get("item_fields") or []
    slugs: list[str] = []
    for field in item_fields:
        if isinstance(field, dict) and field.get("slug"):
            slugs.append(str(field["slug"]))
    return slugs


__all__ = ["EDIT_MENU_LABEL", "drive_collection_edit"]