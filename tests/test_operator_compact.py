"""Tests for compact wizard inspect."""

from __future__ import annotations

from palm.common.operator.compact import compact_job_inspect, compact_wizard_inspect


def _sample_view() -> dict:
    return {
        "instance_id": "inst-1",
        "job_id": "job-1",
        "flow_name": "capture",
        "status": "WAITING_FOR_INPUT",
        "current_step_slug": "relationship_phase",
        "prompt": {
            "step": "relationship_phase",
            "text": "Waiting for nested wizard…",
            "field_type": "resource",
            "step_kind": "resource",
            "validation_error": None,
            "waiting_for_child": True,
            "waiting_for_child_job_id": "child-job",
            "waiting_for_child_instance_id": "inst-child",
            "child_status": "WAITING_FOR_INPUT",
            "choices": ["yes", "no"],
        },
        "answers": {"intro": "hello", "goal": "x" * 3000},
        "next_actions": [
            {
                "action": "resume_child_wait",
                "method": "POST",
                "path": "/v1/wizards/inst-1/resume-child-wait",
            }
        ],
    }


def test_compact_wizard_inspect_default_shape() -> None:
    payload = compact_wizard_inspect(_sample_view())
    assert payload["instance_id"] == "inst-1"
    assert payload["flow"] == "capture"
    assert payload["step"] == "relationship_phase"
    assert payload["step_kind"] == "resource"
    assert payload["waiting_for_child"] is True
    assert payload["child"]["instance_id"] == "inst-child"
    assert payload["answers_keys"] == ["goal", "intro"]
    assert payload["next_actions"] == ["resume_child_wait"]
    assert len(payload["answers_preview"]["goal"]) == 2001


def test_compact_wizard_inspect_includes_operator_hint() -> None:
    payload = compact_wizard_inspect(_sample_view())
    assert "inst-child" in payload["operator_hint"]


def test_compact_wizard_inspect_verbose_passthrough() -> None:
    view = _sample_view()
    assert compact_wizard_inspect(view, format="verbose") == view


def test_compact_job_inspect_from_context() -> None:
    payload = compact_job_inspect(
        {
            "job_id": "job-1",
            "status": "WAITING_FOR_INPUT",
            "pattern": {
                "pattern": "wizard",
                "step": "step_1",
                "field_type": "text",
                "prompt": "Name?",
                "answers": {"step_0": "ok"},
            },
            "instance": {"instance_id": "inst-1", "flow_name": "onboard"},
            "next_actions": [{"action": "provide_input"}],
        }
    )
    assert payload["job_id"] == "job-1"
    assert payload["instance_id"] == "inst-1"
    assert payload["step"] == "step_1"
    assert payload["answers_keys"] == ["step_0"]
