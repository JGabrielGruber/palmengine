"""Tests for shared flows session input resolution."""

from __future__ import annotations

from palm.common.operator.flows_session_input import (
    apply_flows_session_input,
    prepare_flows_session_input_params,
)


def test_prepare_flows_session_input_params_maps_collection_action() -> None:
    prepared = prepare_flows_session_input_params(
        {"collection_action": "add", "value": "Title"},
    )
    assert prepared["input"] == "add"
    assert prepared["value"] == "Title"


def test_apply_flows_session_input_edit_shortcut() -> None:
    calls: list[object] = []
    phase = "menu"
    field_index = 0

    def get_context() -> dict:
        return {
            "session_id": "inst-1",
            "detail": {
                "prompt": {"collection_phase": phase, "collection_key": "todos"},
                "answers_preview": {"todos": [{"title": "Old", "priority": "medium"}]},
            },
        }

    def provide_input(value: object) -> dict:
        calls.append(value)
        nonlocal phase, field_index
        if value == "Edit an item":
            phase = "field"
            field_index = 0
        elif phase == "field":
            field_index += 1
            if field_index >= 2:
                phase = "menu"
        return {
            "session_id": "inst-1",
            "detail": {
                "prompt": {
                    "collection_phase": phase,
                    "collection_key": "todos",
                    "item_fields": [{"slug": "title"}, {"slug": "priority"}],
                    "collection_field": "title" if field_index == 0 else "priority",
                    "field_type": "text" if field_index == 0 else "choice",
                    "choices": ["low", "medium", "high"] if field_index == 1 else None,
                },
                "answers_preview": {"todos": [{"title": "Old", "priority": "medium"}]},
            },
        }

    apply_flows_session_input(
        get_context,
        provide_input,
        {"edit": {"item_index": 0, "priority": "low"}},
    )
    assert calls[0] == "Edit an item"
    assert calls[1] == "1"
    assert "Old" in calls
    assert "low" in calls


def test_apply_flows_session_input_one_shot_collection_add() -> None:
    calls: list[object] = []
    phase = "menu"

    def get_context() -> dict:
        return {
            "session_id": "inst-1",
            "detail": {
                "prompt": {
                    "step_kind": "collection",
                    "collection_phase": phase,
                },
            },
        }

    def provide_input(value: object) -> dict:
        calls.append(value)
        nonlocal phase
        if value == "Add a new item":
            phase = "field"
        elif phase == "field":
            phase = "menu"
        return {
            "session_id": "inst-1",
            "detail": {
                "prompt": {
                    "step_kind": "collection",
                    "collection_phase": phase,
                },
            },
        }

    apply_flows_session_input(
        get_context,
        provide_input,
        {"input": "add", "value": "Title"},
    )
    assert calls == ["Add a new item", "Title"]