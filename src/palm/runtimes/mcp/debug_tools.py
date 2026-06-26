"""Tier 3 MCP tools — debug, lifecycle, and observability over REST."""

from __future__ import annotations

from typing import Any

from palm.common.operator.explain_step import explain_flow_step
from palm.common.operator.snapshots import diff_snapshot_states
from palm.runtimes.mcp.submit_body import submit_body


def register_debug_tools(mcp: Any, rest_client: Any) -> None:
    """Register Phase 4 debug and lifecycle MCP tools."""

    @mcp.tool
    def palm_cancel_job(job_id: str) -> dict[str, Any]:
        """Cancel a non-terminal orchestration job."""
        return rest_client.cancel_job(job_id)

    @mcp.tool
    def palm_submit_process(
        process_name: str | None = None,
        process: dict[str, Any] | None = None,
        job_id: str | None = None,
        by_id: bool = False,
    ) -> dict[str, Any]:
        """Start a multi-flow process via staged plans (prepare + submit)."""
        variants = sum(1 for value in (process_name, process) if value is not None)
        if variants != 1:
            raise ValueError("provide exactly one of process_name or process")
        body: dict[str, Any] = {}
        if process_name is not None:
            body["process_name"] = process_name
            if by_id:
                body["by_id"] = True
        else:
            body["process"] = process
        if job_id is not None:
            body["job_id"] = job_id
        prepared = rest_client.prepare_plans(body)
        plans = prepared.get("plans")
        if not isinstance(plans, list) or not plans:
            raise RuntimeError("prepare_plans returned no plans")
        plan_ids = [str(item["plan_id"]) for item in plans if isinstance(item, dict)]
        return rest_client.submit_plans(plan_ids)

    @mcp.tool
    def palm_trace_events(job_id: str, limit: int = 20) -> dict[str, Any]:
        """Recent wizard/instance events from job context."""
        context = rest_client.get_job_context(job_id)
        events = context.get("recent_events")
        if not isinstance(events, list):
            events = []
        trimmed = events[-limit:] if limit > 0 else events
        return {
            "job_id": job_id,
            "count": len(trimmed),
            "events": trimmed,
        }

    @mcp.tool
    def palm_diff_snapshots(
        instance_id: str,
        from_snapshot: str,
        to_snapshot: str,
    ) -> dict[str, Any]:
        """Diff blackboard state between two instance snapshots."""
        before = rest_client.get_snapshot(instance_id, from_snapshot)
        after = rest_client.get_snapshot(instance_id, to_snapshot)
        diff = diff_snapshot_states(before, after)
        return {
            "instance_id": instance_id,
            "from_snapshot": from_snapshot,
            "to_snapshot": to_snapshot,
            **diff,
        }

    @mcp.tool
    def palm_explain_step(flow_id: str, step_slug: str) -> dict[str, Any]:
        """Step slug → kind, validation, transform spec, resource_ref from flow definition."""
        flow = rest_client.get_flow(flow_id, verbose=True)
        explained = explain_flow_step(flow, step_slug)
        if explained is None:
            raise ValueError(f"step {step_slug!r} not found in flow {flow_id!r}")
        return explained

    @mcp.tool
    def palm_validate_flow(
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
        return rest_client.validate_flow(body)

    @mcp.tool
    def palm_doctor() -> dict[str, Any]:
        """Engine health: registries, storage, patterns, providers, job counts."""
        return rest_client.get_doctor()

    @mcp.tool
    def palm_fetch_job(job_id: str) -> dict[str, Any]:
        """Fetch compositional child job payload via the palm provider."""
        return rest_client.invoke_resource(
            {
                "resource_ref": "palm",
                "action": "fetch",
                "resource_id": job_id,
            }
        )


__all__ = ["register_debug_tools"]