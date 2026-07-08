"""Design propose → impact → commit via PalmInProcessBackend (MCP path)."""

from __future__ import annotations

from palm.definitions import FlowDefinition
from palm.runtimes.mcp.in_process import create_in_process_backend


def test_design_full_flow_in_process_backend() -> None:
    backend = create_in_process_backend()
    body = FlowDefinition(
        name="mcp-integration-flow",
        pattern="wizard",
        options={"steps": [{"slug": "n", "title": "N", "prompt": "?"}]},
    ).to_dict()
    proposed = backend.design_propose_flow(body=body)
    proposal_id = proposed["proposal"]["proposal_id"]
    assert proposed["validation"]["valid"] is True

    impact = backend.design_analyze_proposal_impact(proposal_id)
    assert impact["target_revision"] == 1

    committed = backend.design_commit_proposal(proposal_id)
    assert committed["revision"] == 1
    assert committed["flow_id"] == "mcp-integration-flow"


def test_design_publish_flow_one_shot() -> None:
    backend = create_in_process_backend()
    body = FlowDefinition(
        name="mcp-publish-one-shot",
        pattern="wizard",
        options={"steps": [{"slug": "n", "title": "N", "prompt": "?"}]},
    ).to_dict()
    result = backend.design_publish_flow(body=body)
    assert result["status"] == "committed"
    assert result["flow_id"] == "mcp-publish-one-shot"
    assert result["revision"] == 1
    tools = {a.get("tool") for a in result.get("actions") or []}
    assert "palm_flows_create_session" in tools