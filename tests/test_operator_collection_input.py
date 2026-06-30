"""Tests for wizard collection action input resolution."""

from __future__ import annotations

import pytest

from palm.common.operator.collection_input import (
    resolve_wizard_collection_action,
    resolve_wizard_form_input,
)


def test_resolve_collection_add() -> None:
    assert resolve_wizard_collection_action("add") == "Add a new item"


def test_resolve_collection_add_with_value_raises() -> None:
    with pytest.raises(ValueError, match="menu-phase"):
        resolve_wizard_collection_action("add", value="main")


def test_resolve_collection_edit() -> None:
    assert resolve_wizard_collection_action("edit", item_index=2) == (
        "__compound_edit__",
        2,
    )


def test_resolve_collection_done_from_choices() -> None:
    wizard = {"prompt": {"choices": ["Continue to summary (3 items)"]}}
    assert (
        resolve_wizard_collection_action("done", wizard_view=wizard)
        == "Continue to summary (3 items)"
    )


def test_resolve_form_input_matches_action() -> None:
    wizard = {"prompt": {"choices": []}}
    form = {"collection_action": "remove", "item_index": "1"}
    assert resolve_wizard_form_input(form, wizard) == ("__compound_remove__", 1)
