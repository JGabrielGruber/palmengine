"""Parallel pattern MCP tools — branch status and merge preview."""

from __future__ import annotations

from typing import Any


def register_parallel_mcp_tools(mcp: Any, rest_client: Any) -> None:
    """Register parallel-specific MCP tools on ``mcp``."""

    @mcp.tool
    def palm_parallel_branch_status(job_id: str) -> dict[str, Any]:
        """Branch slugs, active branch, per-branch steps, and merge preview."""
        context = rest_client.get_job_context(job_id)
        pattern = context.get("pattern")
        if not isinstance(pattern, dict):
            pattern = {}
        if pattern.get("pattern") != "parallel":
            raise ValueError(
                f"job {job_id!r} is not a parallel pattern (got {pattern.get('pattern')!r})"
            )
        instance = context.get("instance")
        if not isinstance(instance, dict):
            instance = {}
        return {
            "job_id": context.get("job_id"),
            "instance_id": instance.get("instance_id"),
            "status": context.get("status"),
            "step": pattern.get("step"),
            "scope_path": pattern.get("scope_path"),
            "active_branch": pattern.get("active_branch"),
            "branch_progress": pattern.get("branch_progress"),
            "branches": pattern.get("branches"),
            "merged": pattern.get("merged"),
        }


__all__ = ["register_parallel_mcp_tools"]
