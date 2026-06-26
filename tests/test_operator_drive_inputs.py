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
        include_steps=True,
    )

    assert result["stopped_reason"] == "terminal"
    assert result["steps_applied"] == 2
    assert result["steps"][0]["step_before"] == "intro"
    assert result["steps"][1]["step_after"] == "done"
    assert "steps" not in drive_wizard_inputs(
        instance_id="inst-1",
        inputs=[],
        get_wizard=lambda _i: views[2],
        provide_input=provide_input,
    )


def test_drive_wizard_inputs_stops_on_succeeded_status() -> None:
    view = {
        "instance_id": "inst-2",
        "status": "SUCCEEDED",
        "current_step_slug": "done",
        "prompt": {"step": "done"},
        "answers": {"goal": "done"},
        "result": {"node": {"id": "node-1"}},
    }

    result = drive_wizard_inputs(
        instance_id="inst-2",
        inputs=["yes"],
        get_wizard=lambda _i: view,
        provide_input=lambda _i, _v: view,
    )

    assert result["stopped_reason"] == "terminal"
    assert result["steps_applied"] == 0


def test_drive_wizard_inputs_uses_payload_before_string_inputs() -> None:
    views = [
        {
            "instance_id": "inst-3",
            "status": "WAITING_FOR_INPUT",
            "current_step_slug": "batch_payload",
            "prompt": {"step": "batch_payload", "field_type": "text"},
            "answers": {"goal": "Capture"},
        },
        {
            "instance_id": "inst-3",
            "status": "SUCCEEDED",
            "current_step_slug": "done",
            "prompt": {"step": "done"},
            "answers": {"goal": "Capture", "batch_payload": {"main": {}}},
        },
    ]
    calls: list[object] = []
    current = {"index": 0}

    def get_wizard(_instance_id: str) -> dict:
        return views[current["index"]]

    def provide_input(_instance_id: str, value: object) -> dict:
        calls.append(value)
        current["index"] = 1
        return views[1]

    result = drive_wizard_inputs(
        instance_id="inst-3",
        inputs=['{"ignored": true}'],
        payload={"main": {"title": "Test"}},
        get_wizard=get_wizard,
        provide_input=provide_input,
        include_steps=True,
    )

    assert calls == [{"main": {"title": "Test"}}]
    assert result["stopped_reason"] == "terminal"