"""Tests for definitions service catalog row shapes."""

from __future__ import annotations

from palm.definitions import FlowDefinition, ProcessDefinition
from palm.services.definitions.flows import flow_catalog_row
from palm.services.definitions.processes import process_catalog_row


def test_process_catalog_row_includes_entry_flow() -> None:
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
                            'palm_flows_create_session(flow_name="knowkey_capture_knowledge_batch")'
                        ),
                    }
                }
            },
        },
    )

    summary = process_catalog_row(process)

    assert summary["flow_count"] == 2
    assert summary["entry_flow"] == "knowkey_main_menu"
    assert "submit_hint" not in summary
    assert "avoid" not in summary


def test_flow_catalog_row_includes_wizard_step_slugs() -> None:
    flow = FlowDefinition(
        name="onboard",
        pattern="wizard",
        options={
            "steps": [
                {"slug": "name", "type": "field"},
                {"slug": "confirm", "type": "field"},
            ]
        },
    )

    row = flow_catalog_row(flow)

    assert row["flow_id"] == "onboard"
    assert row["step_slugs"] == ["name", "confirm"]