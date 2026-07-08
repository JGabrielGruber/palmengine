"""Tests for palm_assist dispatch result shaping."""

from __future__ import annotations

from palm.runtimes.mcp.assist.dispatch import (
    resolve_dispatch_format,
    shape_dispatch_result,
)
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
        },
    )


def test_resolve_dispatch_format_assist_defaults_assistant() -> None:
    assert (
        resolve_dispatch_format(["assist", "session", "inst-1"], tool_format="assistant")
        == "assistant"
    )


def test_resolve_dispatch_format_flows_honors_assistant_tool_format() -> None:
    """0.30.6+ — palm_assist passes tool_format=assistant for flows paths."""
    assert (
        resolve_dispatch_format(
            ["flows", "onboard", "session", "inst-1"],
            tool_format="assistant",
        )
        == "assistant"
    )


def test_resolve_dispatch_format_flows_powertool_when_requested() -> None:
    assert (
        resolve_dispatch_format(
            ["flows", "onboard", "session", "inst-1"],
            params={"format": "powertool"},
            tool_format="assistant",
        )
        == "powertool"
    )


def test_shape_dispatch_result_assistant_passthrough() -> None:
    envelope = {
        "session_id": "inst-1",
        "status": "waiting",
        "question": "Hello?",
        "choices": [{"n": 1, "label": "Yes", "value": "yes"}],
    }
    payload = shape_dispatch_result(
        ["assist", "session", "inst-1"],
        envelope,
        format="assistant",
    )
    assert payload["question"] == "Hello?"
    assert payload["path"] == ["assist", "session", "inst-1"]


def test_shape_dispatch_result_flows_session_assistant_default() -> None:
    from palm.common.operator.view_registry import clear_operator_view_builders
    from palm.services.assist.views import ensure_assist_view_registration

    clear_operator_view_builders()
    ensure_assist_view_registration()
    ctx = _sample_session_context()
    payload = shape_dispatch_result(
        ["flows", "onboard", "session", "inst-1"],
        ctx,
        tool_format="assistant",
    )
    assert payload.get("session_id") == "inst-1" or payload.get("instance_id") == "inst-1"
    assert payload.get("question") == "Welcome"


def test_shape_dispatch_result_flows_session_assistant_opt_in() -> None:
    from palm.common.operator.view_registry import clear_operator_view_builders
    from palm.services.assist.views import ensure_assist_view_registration

    clear_operator_view_builders()
    ensure_assist_view_registration()
    ctx = _sample_session_context()
    payload = shape_dispatch_result(
        ["flows", "onboard", "session", "inst-1"],
        ctx,
        params={"format": "assistant"},
    )
    assert payload["question"] == "Welcome"
    assert "operator_hint" not in payload