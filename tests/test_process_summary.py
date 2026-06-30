"""Tests for process catalog summaries."""

from __future__ import annotations

from palm.definitions import FlowDefinition, ProcessDefinition
from palm.runtimes.server.surfaces.rest.serializers import process_summary


def test_process_summary_includes_mcp_entry_hints() -> None:
    process = ProcessDefinition(
        name="knowkey_compose",
        flows=[
            FlowDefinition(name="a", pattern="wizard"),
            FlowDefinition(name="b", pattern="wizard"),
        ],
        metadata={
            "entry_flow": "knowkey_main_menu",
            "mcp": {
                "entries": {
                    "fast": {
                        "flow": "knowkey_capture_knowledge_batch",
                        "submit": (
                            'palm_submit_wizard(flow_name="knowkey_capture_knowledge_batch")'
                        ),
                    }
                }
            },
        },
    )

    summary = process_summary(process)

    assert summary["flow_count"] == 2
    assert summary["entry_flow"] == "knowkey_main_menu"
    assert summary["mcp_default_entry"] == "knowkey_capture_knowledge_batch"
    assert "palm_submit_wizard" in summary["submit_hint"]
    assert "palm_submit_process" in summary["avoid"]
