"""Tests for wizard drive macro."""

from __future__ import annotations

from palm.common.operator.drive_inputs import drive_wizard_inputs


def test_drive_wizard_inputs_applies_sequence() -> None:
    views = [
        {
            "instance_id": "inst-1",
            "status": "WAITING_FOR_INPUT",
            "current_step_slug": "intro",
            "prompt": {"step": "intro", "field_type": "confirm"},
            "answers": {},
        },
        {
            "instance_id": "inst-1",
            "status": "WAITING_FOR_INPUT",
            "current_step_slug": "name",
            "prompt": {"step": "name", "field_type": "text"},
            "answers": {"intro": True},
        },
        {
            "instance_id": "inst-1",
            "status": "SUCCESS",
            "current_step_slug": "done",
            "prompt": {"step": "done"},
            "answers": {"intro": True, "name": "Ada"},
        },
    ]
    calls: list[tuple[str, object]] = []

    def get_wizard(instance_id: str) -> dict:
        return views[min(len(calls), len(views) - 1)]

    def provide_input(instance_id: str, value: object) -> dict:
        calls.append((instance_id, value))
        return views[min(len(calls), len(views) - 1)]

    result = drive_wizard_inputs(
        instance_id="inst-1",
        inputs=["yes", "Ada"],
        get_wizard=get_wizard,
        provide_input=provide_input,
    )

    assert result["stopped_reason"] == "terminal"
    assert result["steps_applied"] == 2
    assert result["steps"][0]["resolved"] is True
    assert result["steps"][1]["resolved"] == "Ada"