"""Design service MCP tools — agent-safe definition evolution."""

from __future__ import annotations

from typing import Any

from palm.runtimes.mcp.descriptions import tool_description

_PALM_DESIGN_PROPOSE_DESC = tool_description(
    "palm_design_propose_flow",
    "Create a design proposal from a wizard flow body (recommended agent catalog write path).",
    when=(
        "Run propose → impact → commit in order. Save ``proposal_id`` from this call. "
        "For revisions, pass ``base_flow_id``. Flow ``name`` must be a slug (``foo-bar``, not spaces). "
        "Load ``palm://agent/references/design-flows`` for a full weak-LLM playbook."
    ),
    examples=[
        'palm_design_propose_flow(body={"name": "foo-bar", "pattern": "wizard", "options": {"steps": [...]}})',
        'palm_design_propose_flow(base_flow_id="foo-bar", body={"name": "foo-bar", "pattern": "wizard", "options": {...}})',
    ],
    use_instead=(
        "Do **not** use ``palm_definitions_*`` create/update for agent catalog writes. "
        "Prefer this tool over editing repo YAML unless the user explicitly asked for file edits."
    ),
    notes=(
        "Each step needs ``slug``, ``title``, ``prompt``. "
        "``field_type: choice`` requires ``choices: [...]``. "
        "Optional: ``palm_design_validate(proposal_id)`` if propose did not return ``valid: true``."
    ),
)

_PALM_DESIGN_LIST_DESC = tool_description(
    "palm_design_list_proposals",
    "List open design proposals, optionally filtered by flow_id.",
    when="Use to resume an in-flight design or check for stale proposals before proposing again.",
    examples=[
        "palm_design_list_proposals()",
        'palm_design_list_proposals(flow_id="foo-bar")',
    ],
)

_PALM_DESIGN_GET_DESC = tool_description(
    "palm_design_get_proposal",
    "Load a design proposal envelope by id.",
    when="Inspect proposal body, validation state, or blockers before impact/commit.",
    examples=[
        'palm_design_get_proposal(proposal_id="prop-...")',
    ],
)

_PALM_DESIGN_VALIDATE_DESC = tool_description(
    "palm_design_validate",
    "Validate a design proposal (catalog build + contributor checks).",
    when="Run when propose returned ``valid: false`` or before impact if unsure.",
    examples=[
        'palm_design_validate(proposal_id="prop-...")',
    ],
    use_instead="Impact also validates; skip if propose already returned ``valid: true`` and you proceed immediately.",
)

_PALM_DESIGN_IMPACT_DESC = tool_description(
    "palm_design_impact",
    "Analyze instance impact for committing a design proposal (required before commit).",
    when=(
        "Always call after propose and **before** commit. "
        "Finished instances may show ``snapshot_only`` — normal; new sessions use the latest revision."
    ),
    examples=[
        'palm_design_impact(proposal_id="prop-...")',
    ],
    notes=(
        "If you see ``No handler registered for AnalyzeDefinitionImpactQuery``, restart ``palm-mcp`` "
        "after upgrading Palm."
    ),
)

_PALM_DESIGN_COMMIT_DESC = tool_description(
    "palm_design_commit",
    "Publish a validated proposal as a new flow revision and auto-migrate compatible instances.",
    when=(
        "Call only after ``palm_design_impact``. Then verify with ``palm_flows_describe(flow_id)`` "
        "or ``palm_flows_list()`` — only committed flows are runnable."
    ),
    examples=[
        'palm_design_commit(proposal_id="prop-...")',
        'palm_design_commit(proposal_id="prop-...", commit_token="<from mutation>")',
    ],
    notes=(
        "When ``PALM_MCP_REQUIRE_INPUT_TOKEN=1``, pass ``commit_token`` from validate/impact ``mutation``."
    ),
)

_PALM_DESIGN_DISCARD_DESC = tool_description(
    "palm_design_discard",
    "Discard an open design proposal.",
    when="Use when abandoning a bad propose or starting over with a fresh body.",
    examples=[
        'palm_design_discard(proposal_id="prop-...")',
    ],
)


def register_design_tools(mcp: Any, backend: Any) -> None:
    """Register design proposal MCP tools."""

    @mcp.tool(description=_PALM_DESIGN_PROPOSE_DESC)
    def palm_design_propose_flow(
        body: dict[str, Any],
        base_flow_id: str | None = None,
    ) -> dict[str, Any]:
        return backend.design_propose_flow(body, base_flow_id=base_flow_id)

    @mcp.tool(description=_PALM_DESIGN_LIST_DESC)
    def palm_design_list_proposals(flow_id: str | None = None) -> dict[str, Any]:
        return backend.design_list_proposals(flow_id=flow_id)

    @mcp.tool(description=_PALM_DESIGN_GET_DESC)
    def palm_design_get_proposal(proposal_id: str) -> dict[str, Any]:
        return backend.design_get_proposal(proposal_id)

    @mcp.tool(description=_PALM_DESIGN_VALIDATE_DESC)
    def palm_design_validate(proposal_id: str) -> dict[str, Any]:
        return backend.design_validate_proposal(proposal_id)

    @mcp.tool(description=_PALM_DESIGN_IMPACT_DESC)
    def palm_design_impact(proposal_id: str) -> dict[str, Any]:
        return backend.design_analyze_proposal_impact(proposal_id)

    @mcp.tool(description=_PALM_DESIGN_COMMIT_DESC)
    def palm_design_commit(
        proposal_id: str,
        commit_token: str | None = None,
        input_token: str | None = None,
    ) -> dict[str, Any]:
        return backend.design_commit_proposal(
            proposal_id,
            commit_token=commit_token,
            input_token=input_token,
        )

    @mcp.tool(description=_PALM_DESIGN_DISCARD_DESC)
    def palm_design_discard(proposal_id: str) -> dict[str, Any]:
        return backend.design_discard_proposal(proposal_id)


__all__ = ["register_design_tools"]