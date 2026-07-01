"""Tests for wizard collection one-shot drive helpers."""

from __future__ import annotations

from typing import Any

import pytest

from palm.common.operator.collection_drive import (
    COLLECTION_ADD_ONE_SHOT,
    drive_collection_add,
)


def test_drive_collection_add_one_shot_from_menu() -> None:
    calls: list[Any] = []

    def provide(value: Any) -> dict[str, Any]:
        calls.append(value)
        if len(calls) == 1:
            return {
                "prompt": {
                    "step_kind": "collection",
                    "collection_phase": "field",
                    "collection_field": "title",
                }
            }
        return {
            "prompt": {"step_kind": "collection", "collection_phase": "menu"},
            "status": "WAITING_FOR_INPUT",
        }

    result = drive_collection_add(provide, value="Test Palm")
    assert calls == ["Add a new item", "Test Palm"]
    assert result["prompt"]["collection_phase"] == "menu"


def test_drive_collection_add_from_field_phase_only() -> None:
    calls: list[Any] = []

    def provide(value: Any) -> dict[str, Any]:
        calls.append(value)
        return {"prompt": {"collection_phase": "menu"}}

    wizard = {
        "prompt": {
            "step_kind": "collection",
            "collection_phase": "field",
            "collection_field": "title",
        }
    }
    result = drive_collection_add(provide, value="Only field", wizard_view=wizard)
    assert calls == ["Only field"]
    assert result["prompt"]["collection_phase"] == "menu"


def test_drive_collection_add_unexpected_phase_raises() -> None:
    wizard = {"prompt": {"collection_phase": "select_item"}}

    with pytest.raises(ValueError, match="field phase"):
        drive_collection_add(lambda _v: {}, value="x", wizard_view=wizard)


def test_collection_add_one_shot_sentinel_is_stable() -> None:
    assert COLLECTION_ADD_ONE_SHOT == "__collection_add_one_shot__"