"""Core MCP operator tools — wired to the Palm REST backend."""

from __future__ import annotations

from typing import Any

from palm.common.operator.compact import compact_job_inspect, compact_wizard_inspect
from palm.common.operator.input_coercion import resolve_mcp_job_input, resolve_mcp_wizard_input
from palm.runtimes.mcp.submit_body import submit_body


def register_core_tools(mcp: Any, rest_client: Any) -> None:
    """Register Tier 1-2 operator MCP tools."""

    @mcp.tool
    def palm_list_waiting(
        pattern: str | None = None,
        flow: str | None = None,
        limit: int = 50,
    ) -> dict[str, Any]:
        """List jobs waiting for interactive input."""
        payload = rest_client.list_waiting_jobs(limit=limit)
        jobs = payload.get("jobs")
        if not isinstance(jobs, list):
            jobs = []
        raw_rows = [row for row in jobs if isinstance(row, dict)]
        if pattern:
            needle = pattern.lower()
            raw_rows = [
                row
                for row in raw_rows
                if needle
                in str((row.get("metadata") or {}).get("pattern", "")).lower()
            ]
        if flow:
            needle = flow.lower()
            raw_rows = [
                row
                for row in raw_rows
                if needle
                in str((row.get("metadata") or {}).get("flow_name", "")).lower()
                or needle in str((row.get("metadata") or {}).get("flow", "")).lower()
            ]
        rows = [_slim_waiting_row(row) for row in raw_rows]
        return {"jobs": rows, "count": len(rows)}

    @mcp.tool
    def palm_inspect_instance(
        instance_id: str,
        format: str = "compact",
        include: list[str] | None = None,
        truncate_answers_at: int = 2000,
    ) -> dict[str, Any]:
        """Compact wizard view: step, prompt, child-wait, and answer keys."""
        view = rest_client.get_wizard(instance_id)
        return compact_wizard_inspect(
            view,
            format=format,
            include=include,
            truncate_answers_at=truncate_answers_at,
        )

    @mcp.tool
    def palm_wizard_input(
        instance_id: str,
        input: str | None = None,
        value: str | int | float | bool | None = None,
    ) -> dict[str, Any]:
        """Deliver interactive input. Use plain ``input`` (text, choice slug, yes/no)—not JSON."""
        view = rest_client.get_wizard(instance_id)
        resolved = resolve_mcp_wizard_input(input=input, value=value, wizard_view=view)
        view = rest_client.provide_wizard_input(instance_id, resolved)
        return compact_wizard_inspect(view)

    @mcp.tool
    def palm_resume_child_wait(instance_id: str) -> dict[str, Any]:
        """Re-check nested child wizard and advance parent when ready."""
        view = rest_client.resume_child_wait(instance_id)
        return compact_wizard_inspect(view)

    @mcp.tool
    def palm_resume_wizard_tick(instance_id: str) -> dict[str, Any]:
        """Re-drive a waiting wizard (for example auto-run a resource step)."""
        view = rest_client.resume_wizard_tick(instance_id)
        return compact_wizard_inspect(view)

    @mcp.tool
    def palm_wizard_backtrack(instance_id: str, to_step: str | None = None) -> dict[str, Any]:
        """Backtrack a wizard to a prior step (omit to_step for previous step)."""
        view = rest_client.backtrack_wizard(instance_id, to_step=to_step)
        return compact_wizard_inspect(view)

    @mcp.tool
    def palm_inspect_job(
        job_id: str,
        format: str = "compact",
        include: list[str] | None = None,
        truncate_answers_at: int = 2000,
    ) -> dict[str, Any]:
        """Compact job context when only job_id is known."""
        context = rest_client.get_job_context(job_id)
        return compact_job_inspect(
            context,
            format=format,
            include=include,
            truncate_answers_at=truncate_answers_at,
        )

    @mcp.tool
    def palm_provide_job_input(
        job_id: str,
        input: str | None = None,
        value: str | int | float | bool | None = None,
    ) -> dict[str, Any]:
        """Deliver interactive input by job_id. Prefer plain ``input`` strings—not JSON."""
        context = rest_client.get_job_context(job_id)
        resolved = resolve_mcp_job_input(input=input, value=value, job_context=context)
        result = rest_client.provide_job_input(job_id, resolved)
        context = rest_client.get_job_context(job_id)
        payload = compact_job_inspect(context)
        if result.get("slug"):
            payload["slug"] = result["slug"]
        return payload

    @mcp.tool
    def palm_submit_wizard(
        flow_name: str | None = None,
        wizard: dict[str, Any] | None = None,
        flow: dict[str, Any] | None = None,
        job_id: str | None = None,
    ) -> dict[str, Any]:
        """Start a wizard flow; returns instance_id and job_id."""
        body = submit_body(flow_name=flow_name, wizard=wizard, flow=flow, job_id=job_id)
        return rest_client.submit_wizard(body)

    @mcp.tool
    def palm_submit_flow(
        flow_name: str | None = None,
        wizard: dict[str, Any] | None = None,
        flow: dict[str, Any] | None = None,
        job_id: str | None = None,
        by_id: bool = False,
    ) -> dict[str, Any]:
        """Submit a flow or wizard as a job."""
        body = submit_body(
            flow_name=flow_name,
            wizard=wizard,
            flow=flow,
            job_id=job_id,
            by_id=by_id,
        )
        return rest_client.submit_flow(body)


def _slim_waiting_row(row: dict[str, Any]) -> dict[str, Any]:
    metadata = row.get("metadata")
    if not isinstance(metadata, dict):
        metadata = {}
    instance_id = metadata.get("instance_id") or row.get("job_id")
    return {
        "job_id": row.get("job_id"),
        "instance_id": instance_id,
        "status": row.get("status"),
        "pattern": metadata.get("pattern"),
        "flow": metadata.get("flow_name") or metadata.get("flow"),
        "step": metadata.get("step") or metadata.get("wizard_step_slug"),
    }


__all__ = ["register_core_tools"]