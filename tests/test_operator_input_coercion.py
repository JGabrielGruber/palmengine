"""Tests for operator input coercion helpers."""

from __future__ import annotations

from palm.common.operator.input_coercion import (
    coerce_job_input,
    resolve_mcp_job_input,
    resolve_mcp_wizard_input,
)


def test_coerce_confirm_yes_to_bool() -> None:
    assert coerce_job_input("yes", {"field_type": "confirm"}) is True
    assert coerce_job_input("no", {"field_type": "confirm"}) is False


def test_coerce_plain_text_unchanged() -> None:
    assert coerce_job_input("Ada Lovelace", {"field_type": "text"}) == "Ada Lovelace"


def test_resolve_mcp_wizard_input_prefers_plain_input() -> None:
    wizard = {
        "prompt": {"field_type": "text"},
        "answers": {},
    }
    assert resolve_mcp_wizard_input(input="Ada", value=None, wizard_view=wizard) == "Ada"


def test_resolve_mcp_wizard_input_confirm_string() -> None:
    wizard = {"prompt": {"field_type": "confirm"}, "answers": {}}
    assert resolve_mcp_wizard_input(input="yes", value=None, wizard_view=wizard) is True


def test_resolve_mcp_job_input_confirm_string() -> None:
    context = {"pattern": {"field_type": "confirm"}}
    assert resolve_mcp_job_input(input="yes", value=None, job_context=context) is True


def test_resolve_mcp_wizard_input_collection_field_bypasses_action_routing() -> None:
    wizard = {
        "prompt": {
            "field_type": "text",
            "step_kind": "collection",
            "collection_phase": "field",
        },
        "answers": {},
    }
    assert resolve_mcp_wizard_input(input="main", value=None, wizard_view=wizard) == "main"


def test_resolve_mcp_wizard_input_collection_menu_accepts_done_label() -> None:
    wizard = {
        "prompt": {
            "field_type": "choice",
            "step_kind": "collection",
            "collection_phase": "menu",
            "choices": ["Add a new item", "Continue to summary (2 items)"],
        },
        "answers": {},
    }
    assert (
        resolve_mcp_wizard_input(input="Continue to summary", value=None, wizard_view=wizard)
        == "Continue to summary (2 items)"
    )


def test_resolve_mcp_wizard_input_collection_menu_add_with_value_one_shot() -> None:
    from palm.common.operator.collection_drive import COLLECTION_ADD_ONE_SHOT

    wizard = {
        "prompt": {
            "field_type": "choice",
            "step_kind": "collection",
            "collection_phase": "menu",
            "choices": ["Add a new item", "Continue to summary"],
        },
        "answers": {},
    }
    assert resolve_mcp_wizard_input(input="add", value="Title", wizard_view=wizard) == (
        COLLECTION_ADD_ONE_SHOT,
        "Title",
    )


def test_coerce_priority_choice_from_intent() -> None:
    from palm.common.operator.input_coercion import coerce_priority_choice

    assert coerce_priority_choice("high priority", ["low", "medium", "high"]) == "high"
    assert coerce_priority_choice("LOW", ["low", "medium", "high"]) == "low"


def test_resolve_mcp_wizard_input_collection_field_priority_intent() -> None:
    wizard = {
        "prompt": {
            "field_type": "choice",
            "step_kind": "collection",
            "collection_phase": "field",
            "collection_field": "priority",
            "choices": ["low", "medium", "high"],
        },
        "answers": {},
    }
    assert resolve_mcp_wizard_input(input="high priority", value=None, wizard_view=wizard) == "high"


def test_resolve_mcp_wizard_input_collection_menu_routes_add_action() -> None:
    wizard = {
        "prompt": {
            "field_type": "choice",
            "step_kind": "collection",
            "collection_phase": "menu",
        },
        "answers": {},
    }
    assert resolve_mcp_wizard_input(input="add", value=None, wizard_view=wizard) == "Add a new item"
