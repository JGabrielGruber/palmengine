"""Integration tests for palm-operator-entry assist scenario."""

from __future__ import annotations

from collections.abc import Iterator

import pytest

from palm.app import ApplicationHost, HostProfile
from palm.app.settings import PalmSettings
from palm.core.orchestration import JobStatus


@pytest.fixture
def assist_host() -> Iterator[ApplicationHost]:
    settings = PalmSettings.for_tests(load_examples=True)
    host = ApplicationHost(settings=settings, profile=HostProfile.all_in_one())
    host.start()
    yield host
    host.shutdown()


def _drive_to_handoff(host: ApplicationHost, session_id: str, intent: str) -> None:
    host.assist.dispatch(["assist", "session", session_id, "input"], {"value": intent})
    ctx = host.assist.dispatch(["assist", "session", session_id])
    if ctx.get("waiting_for_input"):
        host.assist.dispatch(["assist", "session", session_id, "input"], {"value": "yes"})


def test_operator_entry_handoff_recommends_flow(assist_host: ApplicationHost) -> None:
    started = assist_host.assist.start_scenario("operator-entry", {})
    session_id = started["session_id"]
    _drive_to_handoff(assist_host, session_id, "todo-builder")
    handoff = assist_host.assist.handoff(session_id)
    assert handoff["handoff"]["kind"] == "flow"
    assert handoff["handoff"]["flow_id"] == "todo-builder"


def test_operator_entry_inspect_only_handoff_none(assist_host: ApplicationHost) -> None:
    started = assist_host.assist.start_scenario("operator-entry", {})
    session_id = started["session_id"]
    assist_host.assist.dispatch(
        ["assist", "session", session_id, "input"],
        {"value": "inspect-only"},
    )
    handoff = assist_host.assist.handoff(session_id)
    assert handoff["handoff"]["kind"] == "none"
    assert handoff["handoff"]["flow_id"] is None


def test_operator_entry_create_flow_actions_after_to_dict(
    assist_host: ApplicationHost,
) -> None:
    started = assist_host.assist.start_scenario("operator-entry", {})
    session_id = started["session_id"]
    # Land on summary with create-flow intent
    updated = assist_host.assist.dispatch(
        ["assist", "session", session_id, "input"],
        {"value": "create-flow"},
    )
    assert updated.get("status") in {"waiting", "complete"}
    actions = updated.get("actions") or []
    tools = {a.get("tool") for a in actions if isinstance(a, dict)}
    aliases = {a.get("alias") for a in actions if isinstance(a, dict)}
    assert "palm_design_propose_flow" in tools or "design/propose" in aliases
    assert "palm_design_propose_flow" in (updated.get("hint") or "") or "design" in (
        updated.get("hint") or ""
    ).lower()


def test_operator_entry_create_flow_handoff_none_hint(
    assist_host: ApplicationHost,
) -> None:
    started = assist_host.assist.start_scenario("operator-entry", {})
    session_id = started["session_id"]
    _drive_to_handoff(assist_host, session_id, "create-flow")
    handoff = assist_host.assist.handoff(session_id)
    assert handoff["handoff"]["kind"] == "none"
    assert handoff["handoff"]["flow_id"] is None
    hint = handoff["handoff"]["operator_hint"]
    assert "palm_design_propose_flow" in hint
    assert "no business flow handoff" not in hint.lower() or "Design" in hint or "design" in hint


def test_operator_entry_start_includes_design_choices(
    assist_host: ApplicationHost,
) -> None:
    started = assist_host.assist.start_scenario("operator-entry", {})
    choices = started.get("choices") or []
    values = {
        c.get("value") if isinstance(c, dict) else c
        for c in choices
    }
    assert "create-flow" in values
    assert "improve-flow" in values