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
    assert result.get("status") == "waiting"
    assert "detail" not in result


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