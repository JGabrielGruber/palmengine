"""Definitions service MCP tools."""

from __future__ import annotations

from typing import Any

from palm.common.operator.explain_step import explain_flow_step
from palm.runtimes.mcp.submit_body import submit_body


def register_definitions_tools(mcp: Any, backend: Any) -> None:
    """Register definition catalog MCP tools."""

    @mcp.tool
    def palm_definitions_validate_flow(
        flow_name: str | None = None,
        wizard: dict[str, Any] | None = None,
        flow: dict[str, Any] | None = None,
        by_id: bool = False,
    ) -> dict[str, Any]:
        """Dry-run flow definition build without submitting a job."""
        body = submit_body(
            flow_name=flow_name,
            wizard=wizard,
            flow=flow,
            job_id=None,
            by_id=by_id,
        )
        return backend.validate_flow(body)

    @mcp.tool
    def palm_definitions_explain_step(flow_id: str, step_slug: str) -> dict[str, Any]:
        """Step slug → kind, validation, transform spec, resource_ref from flow definition."""
        flow = backend.get_flow(flow_id, verbose=True)
        explained = explain_flow_step(flow, step_slug)
        if explained is None:
            raise ValueError(f"step {step_slug!r} not found in flow {flow_id!r}")
        return explained


__all__ = ["register_definitions_tools"]