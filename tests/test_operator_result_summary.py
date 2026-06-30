"""Tests for commit result summaries."""

from __future__ import annotations

from palm.common.operator.result_summary import summarize_commit_result


def test_summarize_commit_result_extracts_main_and_related_ids() -> None:
    result = {
        "main_node": {"id": "node-main", "title": "MCP Servers for LLMs"},
        "captured_nodes": [
            {"id": "node-related-1", "title": "Schema Discovery"},
            {"id": "node-related-2", "title": "Resources vs Tools"},
        ],
    }

    summary = summarize_commit_result(result)

    assert summary is not None
    assert summary["main_node_id"] == "node-main"
    assert summary["main_node_title"] == "MCP Servers for LLMs"
    assert summary["node_ids"] == ["node-related-1", "node-related-2"]
