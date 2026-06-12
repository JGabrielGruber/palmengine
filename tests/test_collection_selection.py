"""Tests for collection item selection helpers."""

from __future__ import annotations

from palm.patterns.wizard.collection_selection import (
    default_label_field,
    format_numbered_item_list,
    is_cancel_input,
    resolve_item_index,
)


def test_resolve_item_by_number() -> None:
    items = [{"title": "Buy milk"}, {"title": "Walk dog"}]
    assert resolve_item_index("2", items, label_field="title") == 1


def test_resolve_item_by_partial_label() -> None:
    items = [{"title": "Buy milk"}, {"title": "Walk dog"}]
    assert resolve_item_index("milk", items, label_field="title") == 0


def test_resolve_item_cancel_input() -> None:
    assert is_cancel_input("cancel")
    assert is_cancel_input("C")
    assert not is_cancel_input("milk")


def test_default_label_field_prefers_required_text() -> None:
    from palm.patterns.wizard.collection import CollectionFieldConfig

    fields = (
        CollectionFieldConfig(slug="title", title="Title", prompt="?", required=True),
        CollectionFieldConfig(
            slug="priority",
            title="Priority",
            prompt="?",
            field_type="choice",
            choices=("low", "high"),
        ),
    )
    assert default_label_field(fields, None) == "title"
    assert default_label_field(fields, "priority") == "priority"


def test_format_numbered_item_list_truncates_long_titles() -> None:
    items = [{"title": "A" * 50, "priority": "high"}]
    listing = format_numbered_item_list(items, label_field="title")
    assert listing.startswith("1.")
    assert "…" in listing