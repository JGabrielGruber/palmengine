"""Integration tests for palm-operator-entry assist scenario."""

from __future__ import annotations

from collections.abc import Iterator

import pytest

from palm.app import ApplicationHost, HostProfile
from palm.app.settings import PalmSettings


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
    # Demo flows skip summary (0.32.5); design intents may also be terminal.
    if ctx.get("waiting_for_input") or ctx.get("status") == "waiting":
        host.assist.dispatch(["assist", "session", session_id, "input"], {"value": "yes"})


def test_operator_entry_handoff_recommends_flow(assist_host: ApplicationHost) -> None:
    started = assist_host.assist.start_scenario("operator-entry", {})
    session_id = started["session_id"]
    updated = assist_host.assist.dispatch(
        ["assist", "session", session_id, "input"],
        {"value": "todo-builder"},
    )
    # 0.32.5 — skip summary; terminal with Start Todo Builder CTA
    assert updated.get("status") == "complete"
    assert updated.get("handoff_ready") is True
    labels = [a.get("label") for a in (updated.get("actions") or []) if isinstance(a, dict)]
    assert any(isinstance(lbl, str) and "Todo Builder" in lbl for lbl in labels)
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
    # 0.30.5: create-flow skips summary → terminal with design CTAs
    updated = assist_host.assist.dispatch(
        ["assist", "session", session_id, "input"],
        {"value": "create-flow"},
    )
    assert updated.get("status") == "complete"
    assert updated.get("mutation", {}).get("confirm_step") is not True
    actions = updated.get("actions") or []
    tools = {a.get("tool") for a in actions if isinstance(a, dict)}
    assert "palm_design_publish_flow" in tools
    assert "publish" in (updated.get("hint") or "").lower()
    labels = [a.get("label") for a in actions if isinstance(a, dict)]
    assert labels and "Publish" in str(labels[0])


def test_operator_entry_create_flow_handoff_kind_design(
    assist_host: ApplicationHost,
) -> None:
    started = assist_host.assist.start_scenario("operator-entry", {})
    session_id = started["session_id"]
    _drive_to_handoff(assist_host, session_id, "create-flow")
    handoff = assist_host.assist.handoff(session_id)
    assert handoff["handoff"]["kind"] == "design"
    assert handoff["handoff"]["flow_id"] is None
    assert handoff["handoff"]["design_action"] == "publish_flow"
    assert handoff["handoff"]["intent"] == "create-flow"
    hint = handoff["handoff"]["operator_hint"]
    assert "palm_design_publish_flow" in hint


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
    assert "coconut-npc" in values
    assert "propose-resource" in values


def test_operator_entry_coconut_handoff(assist_host: ApplicationHost) -> None:
    started = assist_host.assist.start_scenario("operator-entry", {})
    session_id = started["session_id"]
    _drive_to_handoff(assist_host, session_id, "coconut-npc")
    handoff = assist_host.assist.handoff(session_id)
    assert handoff["handoff"]["kind"] == "flow"
    assert handoff["handoff"]["flow_id"] == "coconut-npc"


def test_operator_entry_demo_flow_skips_summary(assist_host: ApplicationHost) -> None:
    """0.32.5 — todo-builder completes without summary confirm; Start CTA first."""
    started = assist_host.assist.start_scenario("operator-entry", {})
    session_id = started["session_id"]
    updated = assist_host.assist.dispatch(
        ["assist", "session", session_id, "input"],
        {"value": "todo-builder"},
    )
    assert updated.get("status") == "complete"
    assert updated.get("mutation", {}).get("confirm_step") is not True
    assert "Ready to start" in str(updated.get("question") or "")
    labels = [a.get("label") for a in (updated.get("actions") or []) if isinstance(a, dict)]
    assert labels and "Todo Builder" in str(labels[0])