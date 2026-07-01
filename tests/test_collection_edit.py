"""Tests for collection compound edit driving."""

from __future__ import annotations

from typing import Any

import pytest

from palm.common.operator.collection_edit import drive_collection_edit


def test_drive_collection_edit_fields() -> None:
    calls: list[Any] = []
    phase = "menu"
    field_index = 0
    field_slugs = ["title", "priority"]

    def provide(value: Any) -> dict[str, Any]:
        calls.append(value)
        nonlocal phase, field_index
        if value == "Edit an item":
            phase = "select_item"
        elif phase == "select_item":
            phase = "field"
            field_index = 0
        elif phase == "field":
            field_index += 1
            if field_index >= len(field_slugs):
                phase = "menu"
        return {
            "prompt": {
                "collection_phase": phase,
                "collection_key": "todos",
                "item_fields": [
                    {"slug": "title"},
                    {"slug": "priority", "field_type": "choice", "choices": ["low", "medium", "high"]},
                ],
                "collection_field": field_slugs[min(field_index, len(field_slugs) - 1)]
                if phase == "field"
                else None,
                "field_type": "choice" if phase == "field" and field_index == 1 else "text",
                "choices": ["low", "medium", "high"] if phase == "field" and field_index == 1 else None,
            },
            "answers_preview": {
                "todos": [{"title": "Old", "priority": "medium"}],
            },
        }

    drive_collection_edit(
        provide,
        item_index=0,
        fields={"title": "Test Palm", "priority": "high"},
        wizard_view={
            "prompt": {
                "collection_phase": "menu",
                "collection_key": "todos",
                "choices": ["Edit an item"],
            },
            "answers_preview": {"todos": [{"title": "Old", "priority": "medium"}]},
        },
    )
    assert calls[0] == "Edit an item"
    assert calls[1] == "1"
    assert "Test Palm" in calls
    assert "high" in calls