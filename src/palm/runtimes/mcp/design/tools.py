"""Design service MCP tools — agent-safe definition evolution."""

from __future__ import annotations

from typing import Any


def register_design_tools(mcp: Any, backend: Any) -> None:
    """Register design proposal MCP tools."""

    @mcp.tool
    def palm_design_propose_flow(
        body: dict[str, Any],
        base_flow_id: str | None = None,
    ) -> dict[str, Any]:
        """Create a design proposal from a flow definition body (recommended agent write path)."""
        return backend.design_propose_flow(body, base_flow_id=base_flow_id)

    @mcp.tool
    def palm_design_list_proposals(flow_id: str | None = None) -> dict[str, Any]:
        """List open design proposals, optionally filtered by flow_id."""
        return backend.design_list_proposals(flow_id=flow_id)

    @mcp.tool
    def palm_design_get_proposal(proposal_id: str) -> dict[str, Any]:
        """Load a design proposal envelope by id."""
        return backend.design_get_proposal(proposal_id)

    @mcp.tool
    def palm_design_validate(proposal_id: str) -> dict[str, Any]:
        """Validate a design proposal (catalog build + contributor checks)."""
        return backend.design_validate_proposal(proposal_id)

    @mcp.tool
    def palm_design_impact(proposal_id: str) -> dict[str, Any]:
        """Analyze instance impact for committing a design proposal."""
        return backend.design_analyze_proposal_impact(proposal_id)

    @mcp.tool
    def palm_design_commit(
        proposal_id: str,
        commit_token: str | None = None,
        input_token: str | None = None,
    ) -> dict[str, Any]:
        """Publish a validated proposal as a new flow revision and auto-migrate compatible instances."""
        return backend.design_commit_proposal(
            proposal_id,
            commit_token=commit_token,
            input_token=input_token,
        )

    @mcp.tool
    def palm_design_discard(proposal_id: str) -> dict[str, Any]:
        """Discard an open design proposal."""
        return backend.design_discard_proposal(proposal_id)


__all__ = ["register_design_tools"]