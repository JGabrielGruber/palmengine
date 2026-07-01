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