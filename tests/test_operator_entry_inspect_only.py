"""Integration tests for operator-entry inspect-only catalog mode (0.23.1)."""

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


def test_inspect_only_stays_waiting_after_intent(assist_host: ApplicationHost) -> None:
    started = assist_host.assist.start_scenario("operator-entry", {})
    session_id = started["session_id"]
    assist_host.assist.dispatch(
        ["assist", "session", session_id, "input"],
        {"value": "inspect-only"},
    )
    ctx = assist_host.assist.dispatch(
        ["assist", "session", session_id],
        {"format": "assistant"},
    )
    assert ctx.get("status") == "waiting"
    meta = assist_host.execution.flows.get_instance_metadata(session_id)
    assert meta.get("operator_mode") == "inspect"
    step = (ctx.get("mutation") or {}).get("step_slug")
    assert step == "catalog"
    mutation = ctx.get("mutation") or {}
    assert mutation.get("confirm_step") is not True


def test_inspect_only_exit_completes(assist_host: ApplicationHost) -> None:
    started = assist_host.assist.start_scenario("operator-entry", {})
    session_id = started["session_id"]
    assist_host.assist.dispatch(
        ["assist", "session", session_id, "input"],
        {"value": "inspect-only"},
    )
    assist_host.assist.dispatch(
        ["assist", "session", session_id, "input"],
        {"value": "exit"},
    )
    ctx = assist_host.assist.dispatch(["assist", "session", session_id])
    assert ctx.get("status") in {JobStatus.SUCCEEDED.value, "SUCCEEDED", "complete"}


def test_operator_entry_inspect_alias_read_only(assist_host: ApplicationHost) -> None:
    payload = assist_host.assist.dispatch(
        ["assist", "scenarios", "operator-entry", "inspect"],
        {"format": "assistant"},
    )
    assert payload.get("operator_mode") == "inspect"
    assert payload.get("mutation", {}).get("mutations_allowed") is False
    assert payload.get("flows")
    assert payload.get("actions")


def test_todo_builder_still_reaches_summary(assist_host: ApplicationHost) -> None:
    started = assist_host.assist.start_scenario("operator-entry", {})
    session_id = started["session_id"]
    assist_host.assist.dispatch(
        ["assist", "session", session_id, "input"],
        {"value": "todo-builder"},
    )
    ctx = assist_host.assist.dispatch(
        ["assist", "session", session_id],
        {"format": "assistant"},
    )
    step = (ctx.get("mutation") or {}).get("step_slug")
    assert step == "summary"
    assert ctx.get("mutation", {}).get("confirm_step") is True