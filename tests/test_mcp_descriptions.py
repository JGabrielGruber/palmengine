"""Tests for MCP tool description helpers."""

from __future__ import annotations

from palm.runtimes.mcp.descriptions import tool_description


def test_tool_description_includes_connected_tool_prefix() -> None:
    text = tool_description(
        "palm_assist",
        "Primary Palm entry.",
        examples=["palm_assist()"],
    )
    assert 'call_connected_tool(tool_name="palm___palm_assist"' in text
    assert "Primary Palm entry." in text
    assert "palm_assist()" in text


def test_tool_description_honors_existing_prefix() -> None:
    text = tool_description("palm___palm_flows_list", "List flows.")
    assert 'call_connected_tool(tool_name="palm___palm_flows_list"' in text