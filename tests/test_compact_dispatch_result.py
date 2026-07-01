"""Tests for palm_assist compact dispatch result shaping."""

from __future__ import annotations

from palm.common.operator.compact import compact_wizard_inspect
from palm.runtimes.mcp.assist.dispatch import compact_dispatch_result
from palm.runtimes.mcp.flows.views import flatten_session_view
from palm.services.execution.flows.schemas import SessionContext


def _sample_session_context() -> SessionContext:
    return SessionContext(
        session_id="inst-1",
        flow_id="onboard",
        job_id="job-1",
        status="WAITING_FOR_INPUT",
        pattern="wizard",
        waiting_for_input=True,
        detail={
            "instance_id": "inst-1",
            "job_id": "job-1",
            "flow_name": "onboard",
            "status": "WAITING_FOR_INPUT",
            "current_step_slug": "intro",
            "prompt": {
                "step": "intro",
                "text": "Welcome",
                "field_type": "text",
                "step_kind": "input",
            },
            "answers": {"name": "Ada"},
            "next_actions": [{"action": "input", "method": "POST", "path": "/input"}],
        },
    )


def test_compact_dispatch_result_flows_session_context_object() -> None:
    ctx = _sample_session_context()
    payload = compact_dispatch_result(
        ["flows", "onboard", "session", "inst-1"],
        ctx,
    )

    expected = compact_wizard_inspect(flatten_session_view(ctx))
    assert payload["path"] == ["flows", "onboard", "session", "inst-1"]
    assert payload["instance_id"] == "inst-1"
    assert payload["flow"] == "onboard"
    assert payload["step"] == "intro"
    assert payload["step_kind"] == "input"
    assert payload["prompt"] == "Welcome"
    assert "result" not in payload
    assert payload["answers_keys"] == expected["answers_keys"]


def test_compact_dispatch_result_flows_session_input_returns_compact() -> None:
    ctx = _sample_session_context()
    payload = compact_dispatch_result(
        ["flows", "onboard", "session", "inst-1", "input"],
        ctx,
    )

    assert payload["instance_id"] == "inst-1"
    assert payload["step"] == "intro"
    assert "detail" not in payload


def test_compact_dispatch_result_flows_create_uses_submission_view() -> None:
    payload = compact_dispatch_result(
        ["flows", "onboard", "create"],
        {
            "session_id": "inst-2",
            "flow_id": "onboard",
            "job_id": "job-2",
            "status": "WAITING_FOR_INPUT",
        },
    )

    assert payload["session_id"] == "inst-2"
    assert payload["instance_id"] == "inst-2"
    assert "step" not in payload