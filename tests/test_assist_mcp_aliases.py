"""Tests for assist MCP path alias registry."""

from __future__ import annotations

import pytest

from palm.services.assist.registry import (
    AssistContributor,
    clear_assist_contributors,
    register_assist_contributor,
    resolve_mcp_alias,
)


@pytest.fixture(autouse=True)
def _isolate() -> None:
    clear_assist_contributors()
    yield
    clear_assist_contributors()


def test_resolve_alias_with_session_param() -> None:
    register_assist_contributor(
        AssistContributor(
            contributor_id="demo",
            scenario_id="demo",
            flow_id="flow-demo",
            mcp_aliases=(("demo/handoff", ("assist", "session", "{session_id}", "handoff")),),
        )
    )
    path = resolve_mcp_alias("demo/handoff", params={"session_id": "inst-abc"})
    assert path == ("assist", "session", "inst-abc", "handoff")