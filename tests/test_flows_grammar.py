"""Tests for flow command-path grammar."""

from __future__ import annotations

import pytest

from palm.services.execution.flows.grammar import (
    FlowCommandKind,
    command_path,
    normalize_path,
    parse_flow_command,
)


def test_normalize_path_strips_flows_prefix() -> None:
    assert normalize_path(["flows", "approve"]) == ("approve",)
    assert normalize_path(["approve"]) == ("approve",)


def test_parse_list_command() -> None:
    parsed = parse_flow_command(["flows"])
    assert parsed.kind == FlowCommandKind.LIST


def test_parse_describe_command() -> None:
    parsed = parse_flow_command(["flows", "approve"])
    assert parsed.kind == FlowCommandKind.DESCRIBE
    assert parsed.flow_id == "approve"


def test_parse_create_command() -> None:
    parsed = parse_flow_command(["approve", "create"])
    assert parsed.kind == FlowCommandKind.CREATE
    assert parsed.flow_id == "approve"


def test_parse_session_context_command() -> None:
    parsed = parse_flow_command(["flows", "approve", "session", "inst-1"])
    assert parsed.kind == FlowCommandKind.SESSION
    assert parsed.flow_id == "approve"
    assert parsed.session_id == "inst-1"


def test_parse_session_verb_command() -> None:
    parsed = parse_flow_command(["flows", "approve", "session", "inst-1", "input"])
    assert parsed.kind == FlowCommandKind.SESSION_VERB
    assert parsed.verb == "input"


def test_parse_unknown_path_raises() -> None:
    with pytest.raises(ValueError, match="unrecognized flow command path"):
        parse_flow_command(["flows", "approve", "nope"])


def test_command_path_builder() -> None:
    assert command_path(flow_id="approve", session_id="inst-1", verb="input") == [
        "flows",
        "approve",
        "session",
        "inst-1",
        "input",
    ]