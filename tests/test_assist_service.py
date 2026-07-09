"""Tests for AssistService dispatch and session handling."""

from __future__ import annotations

from collections.abc import Iterator

import pytest

from palm.app import ApplicationHost, HostProfile
from palm.app.settings import PalmSettings
from palm.core.orchestration import JobStatus


@pytest.fixture
def assist_settings() -> PalmSettings:
    return PalmSettings.for_tests(load_examples=True)


@pytest.fixture
def assist_host(assist_settings: PalmSettings) -> Iterator[ApplicationHost]:
    host = ApplicationHost(settings=assist_settings, profile=HostProfile.all_in_one())
    host.start()
    yield host
    host.shutdown()


def test_application_host_exposes_assist(assist_host: ApplicationHost) -> None:
    assert assist_host.assist is not None
    assert hasattr(assist_host.assist, "dispatch")


def test_start_operator_entry_returns_first_turn(assist_host: ApplicationHost) -> None:
    result = assist_host.assist.dispatch(
        ["assist", "scenarios", "operator-entry", "start"],
        params={"body": {}},
    )
    assert "session_id" in result
    assert result.get("scenario_id") == "operator-entry"
    assert result.get("question")
    assert result.get("choices")


def test_portal_greeting_shape_preserves_question_and_input(
    assist_host: ApplicationHost,
) -> None:
    """0.32.6 regression: value=Hi + include_input_schema must not lock the chat.

    WebSocket Portal often sends a greeting as params.value on first dispatch.
    Rebuild-from-assistant used to wipe question and set mutations_allowed=false.
    """
    from palm.runtimes.mcp.assist.dispatch import (
        normalize_assist_dispatch_args,
        resolve_dispatch_path,
        dispatch_operator_path,
        shape_dispatch_result,
    )
    from palm.services.assist.views import ensure_assist_view_registration

    ensure_assist_view_registration()
    params = {"value": "Hi", "include_input_schema": True}
    path, alias, p, _ = normalize_assist_dispatch_args(
        path=None, alias=None, params=params
    )
    resolved = resolve_dispatch_path(path=path, alias=alias, params=p)
    raw = dispatch_operator_path(assist_host, resolved, p)
    shaped = shape_dispatch_result(
        resolved,
        raw,
        format="assistant",
        params=p,
        tool_format="assistant",
        include_input_schema=True,
    )
    assert shaped.get("status") == "waiting"
    assert "What would you like" in (shaped.get("question") or "")
    mutation = shaped.get("mutation") or {}
    assert mutation.get("mutations_allowed") is True
    assert mutation.get("requires_user_input") is True
    schema = shaped.get("input")
    assert isinstance(schema, dict)
    assert schema.get("widget") in {"choice", "text"}
    assert shaped.get("choices") or schema.get("choices")
    # MCP default still omits input when flag is off
    shaped_mcp = shape_dispatch_result(
        resolved,
        # re-start without schema flag for a clean MCP-shaped compare
        assist_host.assist.dispatch(
            ["assist", "scenarios", "operator-entry", "start"],
            {"format": "assistant"},
        ),
        format="assistant",
        include_input_schema=False,
    )
    assert "input" not in shaped_mcp or shaped_mcp.get("input") is None


def test_start_operator_entry_powertool_opt_in(assist_host: ApplicationHost) -> None:
    result = assist_host.assist.dispatch(
        ["assist", "scenarios", "operator-entry", "start"],
        params={"body": {}, "format": "powertool"},
    )
    assert result.get("session_id") or result.get("instance_id")
    assert result.get("status") == "WAITING_FOR_INPUT"
    assert "operator_hint" in result
    assert "question" not in result


def test_assist_list_scenarios_includes_operator_entry(assist_host: ApplicationHost) -> None:
    rows = assist_host.assist.dispatch(["assist", "scenarios"])
    ids = {row["scenario_id"] for row in rows}
    assert "operator-entry" in ids


def test_assist_doctor_returns_report(assist_host: ApplicationHost) -> None:
    report = assist_host.assist.dispatch(["assist", "doctor"])
    assert isinstance(report, dict)
    assert "storage" in report or "runtimes" in report or "version" in report


def test_assist_session_includes_actions_block(assist_host: ApplicationHost) -> None:
    started = assist_host.assist.start_scenario("operator-entry", {})
    session_id = started["session_id"]
    assert "actions" in started
    assert any(action.get("label") == "Send answer" for action in started["actions"])


def test_operator_entry_enricher_handoff_cta(assist_host: ApplicationHost) -> None:
    """Demo intents complete without summary; handoff CTA/hint present (0.32.5+)."""
    started = assist_host.assist.start_scenario("operator-entry", {})
    session_id = started["session_id"]
    updated = assist_host.assist.dispatch(
        ["assist", "session", session_id, "input"],
        {"value": "todo-builder", "format": "assistant"},
    )
    assert updated.get("handoff_ready") is True
    assert updated.get("status") == "complete"
    hint = (updated.get("hint") or "").lower()
    actions = updated.get("actions") or []
    labels = " ".join(str(a.get("label") or "") for a in actions if isinstance(a, dict)).lower()
    assert (
        "handoff" in hint
        or "start" in labels
        or any(
            isinstance(a, dict) and (a.get("params") or {}).get("flow_id") == "todo-builder"
            for a in actions
        )
    )


def test_assist_catalog_flows_dispatch(assist_host: ApplicationHost) -> None:
    rows = assist_host.assist.dispatch(["assist", "catalog", "flows"])
    assert isinstance(rows, list)
    assert rows


def test_inspect_catalog_includes_design_cta(assist_host: ApplicationHost) -> None:
    payload = assist_host.assist.inspect_catalog("operator-entry")
    actions = payload.get("actions") or []
    aliases = {a.get("alias") for a in actions if isinstance(a, dict)}
    assert "design/publish" in aliases
    assert "assist/doctor" in aliases
    assert payload.get("mutation", {}).get("mutations_allowed") is False


def test_handoff_todo_builder_still_kind_flow(assist_host: ApplicationHost) -> None:
    started = assist_host.assist.start_scenario("operator-entry", {})
    session_id = started["session_id"]
    assist_host.assist.dispatch(
        ["assist", "session", session_id, "input"],
        {"value": "todo-builder", "format": "assistant"},
    )
    handoff = assist_host.assist.handoff(session_id)
    assert handoff["handoff"]["kind"] == "flow"
    assert handoff["handoff"]["flow_id"] == "todo-builder"


def test_assist_session_input_and_context(assist_host: ApplicationHost) -> None:
    started = assist_host.assist.start_scenario("operator-entry", {})
    session_id = started["session_id"]
    ctx = assist_host.assist.dispatch(["assist", "session", session_id])
    assert ctx["session_id"] == session_id
    assert ctx.get("status") == "waiting"
    assert ctx.get("question")
    assert "detail" not in ctx

    updated = assist_host.assist.dispatch(
        ["assist", "session", session_id, "input"],
        {"value": "todo-builder"},
    )
    assert updated["session_id"] == session_id
    if updated.get("status") == "waiting":
        assist_host.assist.dispatch(
            ["assist", "session", session_id, "input"],
            {"value": "yes"},
        )

    handoff = assist_host.assist.handoff(session_id)
    assert handoff["handoff"]["kind"] == "flow"
    assert handoff["handoff"]["flow_id"] == "todo-builder"