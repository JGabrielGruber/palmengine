"""System service MCP tools — observe, jobs, snapshots."""

from __future__ import annotations

from typing import Any

from palm.common.operator.compact import compact_job_inspect
from palm.common.operator.input_coercion import resolve_mcp_job_input
from palm.common.operator.snapshots import diff_snapshot_states
from palm.common.operator.waiting_jobs import slim_waiting_job_row
from palm.common.operator.process_submit import validate_process_submit
from palm.runtimes.mcp.rest_client import PalmRestError
from palm.runtimes.mcp.descriptions import tool_description
from palm.runtimes.mcp.submit_body import submit_body

_PALM_SYSTEM_DOCTOR_DESC = tool_description(
    "palm_system_doctor",
    "Engine health check — registries, storage, patterns, providers, job counts, resource preflight.",
    when="Run at session start or when REST resource invokes fail (missing base_url).",
    examples=[
        "palm_system_doctor()",
    ],
    notes=(
        "resource_preflight.rest_missing_base_url lists REST definitions needing base_url. "
        "resource_preflight.check_health probes check-health when configured."
    ),
)


def register_system_tools(mcp: Any, backend: Any) -> None:
    """Register system observe and lifecycle MCP tools."""

    @mcp.tool
    def palm_system_list_waiting(
        pattern: str | None = None,
        flow: str | None = None,
        limit: int = 50,
    ) -> dict[str, Any]:
        """List jobs waiting for interactive input."""
        payload = backend.list_waiting_jobs(limit=limit)
        jobs = payload.get("jobs")
        if not isinstance(jobs, list):
            jobs = []
        raw_rows = [row for row in jobs if isinstance(row, dict)]
        if pattern:
            needle = pattern.lower()
            raw_rows = [
                row
                for row in raw_rows
                if needle in str((row.get("metadata") or {}).get("pattern", "")).lower()
            ]
        if flow:
            needle = flow.lower()
            raw_rows = [
                row
                for row in raw_rows
                if needle in str((row.get("metadata") or {}).get("flow_name", "")).lower()
                or needle in str((row.get("metadata") or {}).get("flow", "")).lower()
            ]
        rows = [slim_waiting_job_row(row) for row in raw_rows]
        return {"jobs": rows, "count": len(rows)}

    @mcp.tool
    def palm_system_inspect_job(
        job_id: str,
        format: str = "compact",
        include: list[str] | None = None,
        truncate_answers_at: int = 2000,
    ) -> dict[str, Any]:
        """Compact job context when only job_id is known."""
        context = backend.get_job_context(job_id)
        return compact_job_inspect(
            context,
            format=format,
            include=include,
            truncate_answers_at=truncate_answers_at,
        )

    @mcp.tool
    def palm_system_job_input(
        job_id: str,
        input: str | None = None,
        value: str | int | float | bool | None = None,
    ) -> dict[str, Any]:
        """Deliver interactive input by job_id. Prefer plain ``input`` strings—not JSON."""
        context = backend.get_job_context(job_id)
        resolved = resolve_mcp_job_input(input=input, value=value, job_context=context)
        result = backend.provide_job_input(job_id, resolved)
        context = backend.get_job_context(job_id)
        payload = compact_job_inspect(context)
        if result.get("slug"):
            payload["slug"] = result["slug"]
        return payload

    @mcp.tool(description=_PALM_SYSTEM_DOCTOR_DESC)
    def palm_system_doctor() -> dict[str, Any]:
        return backend.get_doctor()

    @mcp.tool
    def palm_system_cancel_job(job_id: str) -> dict[str, Any]:
        """Cancel a non-terminal orchestration job."""
        return backend.cancel_job(job_id)

    @mcp.tool
    def palm_system_fetch_job(job_id: str) -> dict[str, Any]:
        """Fetch job context including commit result and recent events."""
        return backend.get_job_context(job_id)

    @mcp.tool
    def palm_system_trace_events(job_id: str, limit: int = 20) -> dict[str, Any]:
        """Recent wizard/instance events from job context."""
        context = backend.get_job_context(job_id)
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
    def palm_system_diff_snapshots(
        session_id: str,
        from_snapshot: str,
        to_snapshot: str,
    ) -> dict[str, Any]:
        """Diff blackboard state between two session snapshots."""
        before = backend.get_snapshot(session_id, from_snapshot)
        after = backend.get_snapshot(session_id, to_snapshot)
        diff = diff_snapshot_states(before, after)
        return {
            "session_id": session_id,
            "instance_id": session_id,
            "from_snapshot": from_snapshot,
            "to_snapshot": to_snapshot,
            **diff,
        }

    @mcp.tool
    def palm_processes_submit(
        process_name: str | None = None,
        process: dict[str, Any] | None = None,
        job_id: str | None = None,
        by_id: bool = False,
        mode: str = "default",
    ) -> dict[str, Any]:
        """Start a multi-flow process via staged plans (prepare + submit).

        For interactive entry flows use ``palm_flows_create_session`` instead.
        """
        variants = sum(1 for value in (process_name, process) if value is not None)
        if variants != 1:
            raise ValueError("provide exactly one of process_name or process")
        body: dict[str, Any] = {}
        process_detail: dict[str, Any] | None = None
        if process_name is not None:
            body["process_name"] = process_name
            if by_id:
                body["by_id"] = True
            if mode != "all_flows":
                try:
                    process_detail = backend.get_process(process_name)
                except PalmRestError:
                    process_detail = None
        else:
            body["process"] = process
            if isinstance(process, dict):
                process_detail = process
        if process_detail is not None:
            validate_process_submit(process_detail, mode=mode)
        if job_id is not None:
            body["job_id"] = job_id
        prepared = backend.prepare_plans(body)
        plans = prepared.get("plans")
        if not isinstance(plans, list) or not plans:
            raise RuntimeError("prepare_plans returned no plans")
        plan_ids = [str(item["plan_id"]) for item in plans if isinstance(item, dict)]
        return backend.submit_plans(plan_ids)


__all__ = ["register_system_tools"]