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


def test_start_operator_entry_returns_session(assist_host: ApplicationHost) -> None:
    result = assist_host.assist.dispatch(
        ["assist", "scenarios", "operator-entry", "start"],
        params={"body": {}},
    )
    assert "session_id" in result
    assert result.get("scenario_id") == "operator-entry"


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
    assert ctx.get("waiting_for_input") is True

    updated = assist_host.assist.dispatch(
        ["assist", "session", session_id, "input"],
        {"value": "todo-builder"},
    )
    assert updated["session_id"] == session_id
    if updated.get("waiting_for_input"):
        assist_host.assist.dispatch(
            ["assist", "session", session_id, "input"],
            {"value": "yes"},
        )

    handoff = assist_host.assist.handoff(session_id)
    assert handoff["handoff"]["kind"] == "flow"
    assert handoff["handoff"]["flow_id"] == "todo-builder"