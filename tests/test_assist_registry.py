"""Tests for assist domain registry and command grammar."""

from __future__ import annotations

import pytest

from palm.services.assist.grammar import AssistCommandKind, parse_assist_command
from palm.services.assist.registry import (
    AssistContributor,
    assist_commands,
    clear_assist_contributors,
    list_scenario_rows,
    register_assist_contributor,
    scenario_by_id,
)


@pytest.fixture(autouse=True)
def _isolate_assist_contributors() -> None:
    clear_assist_contributors()
    yield
    clear_assist_contributors()


def test_assist_commands_include_start_and_handoff() -> None:
    ids = {spec.command_id for spec in assist_commands()}
    assert "start_scenario" in ids
    assert "session_handoff" in ids
    assert "list_scenarios" in ids


def test_assist_contributor_registers_scenario() -> None:
    register_assist_contributor(
        AssistContributor(
            contributor_id="test",
            scenario_id="demo",
            flow_id="flow-palm-operator-entry",
            summary="Demo",
        )
    )
    rows = list_scenario_rows()
    assert any(row["scenario_id"] == "demo" for row in rows)
    found = scenario_by_id("demo")
    assert found is not None
    assert found.flow_id == "flow-palm-operator-entry"


def test_parse_assist_start_scenario() -> None:
    parsed = parse_assist_command(["assist", "scenarios", "operator-entry", "start"])
    assert parsed.kind == AssistCommandKind.START_SCENARIO
    assert parsed.scenario_id == "operator-entry"


def test_parse_assist_session_handoff() -> None:
    parsed = parse_assist_command(["assist", "session", "inst-1", "handoff"])
    assert parsed.kind == AssistCommandKind.SESSION_VERB
    assert parsed.session_id == "inst-1"
    assert parsed.verb == "handoff"