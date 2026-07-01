"""Tests for collection assistant actions mapper."""

from __future__ import annotations

from palm.common.operator.collection_actions import build_collection_assistant_actions


def test_build_collection_assistant_actions_menu_phase() -> None:
    actions = build_collection_assistant_actions(
        {
            "collection_phase": "menu",
            "choices": ["Add a new item", "Continue to summary"],
        },
        session_id="inst-1",
        flow_id="todo-builder",
    )
    labels = [entry["label"] for entry in actions]
    assert "Add item" in labels
    assert "Add titled item" in labels
    assert actions[0]["alias"] == "flows/session-input"
    assert actions[0]["params"] == {
        "session_id": "inst-1",
        "flow_id": "todo-builder",
        "input": "add",
    }


def test_build_collection_assistant_actions_skips_non_menu() -> None:
    assert (
        build_collection_assistant_actions(
            {"collection_phase": "field"},
            session_id="inst-1",
            flow_id="todo-builder",
        )
        == []
    )