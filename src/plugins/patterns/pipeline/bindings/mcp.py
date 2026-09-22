"""Pipeline pattern MCP tools — transform step trace from flow definition."""

from __future__ import annotations

from typing import Any


def register_pipeline_mcp_tools(mcp: Any, rest_client: Any) -> None:
    """Register pipeline-specific MCP tools on ``mcp``."""

    @mcp.tool
    def palm_pipeline_step_trace(job_id: str) -> dict[str, Any]:
        """Ordered transform chain for a pipeline job from its flow definition."""
        context = rest_client.get_job_context(job_id)
        metadata = context.get("metadata")
        if not isinstance(metadata, dict):
            metadata = {}
        pattern = context.get("pattern")
        if not isinstance(pattern, dict):
            pattern = {}

        flow_ref = metadata.get("flow_name") or metadata.get("flow") or pattern.get("flow")
        if not flow_ref:
            raise ValueError(f"job {job_id!r} has no flow reference in metadata")

        flow = rest_client.get_flow(str(flow_ref), verbose=True)
        options = flow.get("options")
        if not isinstance(options, dict):
            options = {}
        steps_raw = options.get("steps")
        if not isinstance(steps_raw, list):
            steps_raw = []

        steps: list[dict[str, Any]] = []
        for index, entry in enumerate(steps_raw):
            if not isinstance(entry, dict):
                continue
            steps.append(
                {
                    "index": index,
                    "rule": entry.get("rule") or entry.get("transform"),
                    "source_key": entry.get("source_key") or entry.get("from"),
                    "target_key": entry.get("target_key") or entry.get("to"),
                }
            )

        return {
            "job_id": context.get("job_id"),
            "flow": flow.get("name") or flow_ref,
            "pattern": flow.get("pattern") or "pipeline",
            "step_count": len(steps),
            "steps": steps,
        }


__all__ = ["register_pipeline_mcp_tools"]
