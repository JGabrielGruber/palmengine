"""FastMCP server — Palm operator tools and resources over REST."""

from __future__ import annotations

import json
from typing import Any

from palm.common.operator.compact import compact_job_inspect, compact_wizard_inspect
from palm.runtimes.mcp.config import PalmMcpConfig
from palm.runtimes.mcp.contributors import register_app_mcp_tools, register_pattern_mcp_tools
from palm.runtimes.mcp.debug_tools import register_debug_tools
from palm.runtimes.mcp.phase5_tools import register_phase5_tools
from palm.runtimes.mcp.prompts import register_core_prompts
from palm.runtimes.mcp.rest_client import PalmRestClient, PalmRestError
from palm.runtimes.mcp.submit_body import submit_body

try:
    from fastmcp import FastMCP
except ImportError as exc:  # pragma: no cover - optional extra
    raise ImportError(
        "fastmcp is required for the Palm MCP server. "
        'Install with: pip install "palmengine[mcp]"'
    ) from exc


def create_mcp_server(
    config: PalmMcpConfig | None = None,
    *,
    client: Any | None = None,
) -> FastMCP:
    """Build a FastMCP server wired to a Palm REST backend."""
    resolved = config or PalmMcpConfig.from_env()
    rest_client = client if client is not None else PalmRestClient(resolved)
    mcp = FastMCP("Palm Operator")

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
    def palm_wizard_input(instance_id: str, value: Any) -> dict[str, Any]:
        """Deliver interactive input to a waiting wizard step."""
        view = rest_client.provide_wizard_input(instance_id, value)
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
    def palm_provide_job_input(job_id: str, value: Any) -> dict[str, Any]:
        """Deliver interactive input to a waiting job by job_id."""
        result = rest_client.provide_job_input(job_id, value)
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

    @mcp.resource(
        "palm://agent/guide",
        mime_type="text/plain",
        annotations={"readOnlyHint": True, "idempotentHint": True},
    )
    def agent_guide() -> str:
        """Palm agent guide — llms.txt and operator protocol."""
        if resolved.llms_txt_path is not None:
            return resolved.llms_txt_path.read_text(encoding="utf-8")
        return (
            "Palm operator MCP adapter.\n"
            f"REST base: {resolved.base_url}\n"
            "Set PALM_LLMS_TXT to a local docs/llms.txt path for the full agent guide."
        )

    @mcp.resource(
        "palm://server/health",
        mime_type="application/json",
        annotations={"readOnlyHint": True, "idempotentHint": True},
    )
    def server_health() -> str:
        """Mirror GET /health from the configured Palm server."""
        return json.dumps(rest_client.get_health())

    @mcp.resource(
        "palm://instances/{instance_id}/tree",
        mime_type="application/json",
        annotations={"readOnlyHint": True, "idempotentHint": True},
    )
    def instance_tree(instance_id: str) -> str:
        """Compositional invoke stack for a durable instance."""
        return json.dumps(rest_client.get_instance_tree(instance_id))

    @mcp.resource(
        "palm://definitions/flows",
        mime_type="application/json",
        annotations={"readOnlyHint": True, "idempotentHint": True},
    )
    def definition_flows() -> str:
        """Registered flow catalog (name, pattern, step slugs)."""
        return json.dumps(rest_client.list_flows())

    @mcp.resource(
        "palm://definitions/flows/{flow_id}",
        mime_type="application/json",
        annotations={"readOnlyHint": True, "idempotentHint": True},
    )
    def definition_flow(flow_id: str, verbose: str = "0") -> str:
        """Single flow summary; pass verbose=1 for full definition."""
        return json.dumps(rest_client.get_flow(flow_id, verbose=verbose.strip() == "1"))

    @mcp.resource(
        "palm://definitions/processes",
        mime_type="application/json",
        annotations={"readOnlyHint": True, "idempotentHint": True},
    )
    def definition_processes() -> str:
        """Registered process catalog."""
        return json.dumps(rest_client.list_processes())

    @mcp.resource(
        "palm://definitions/processes/{process_id}",
        mime_type="application/json",
        annotations={"readOnlyHint": True, "idempotentHint": True},
    )
    def definition_process(process_id: str) -> str:
        """Full process definition by id or name."""
        return json.dumps(rest_client.get_process(process_id))

    @mcp.resource(
        "palm://definitions/resources",
        mime_type="application/json",
        annotations={"readOnlyHint": True, "idempotentHint": True},
    )
    def definition_resources() -> str:
        """Resource definition catalog with provider and param metadata."""
        return json.dumps(rest_client.list_resources())

    @mcp.resource(
        "palm://definitions/resources/{resource_ref}",
        mime_type="application/json",
        annotations={"readOnlyHint": True, "idempotentHint": True},
    )
    def definition_resource(resource_ref: str) -> str:
        """Resource params schema, provider, and action by name or id."""
        return json.dumps(rest_client.get_resource(resource_ref))

    @mcp.resource(
        "palm://openapi",
        mime_type="application/json",
        annotations={"readOnlyHint": True, "idempotentHint": True},
    )
    def openapi_document() -> str:
        """Mirror GET /v1/openapi.json."""
        return json.dumps(rest_client.get_openapi())

    register_core_prompts(mcp, resolved, rest_client)
    register_pattern_mcp_tools(mcp, rest_client)
    register_app_mcp_tools(mcp, rest_client)
    register_debug_tools(mcp, rest_client)
    register_phase5_tools(mcp, rest_client)

    mcp._palm_client = rest_client  # type: ignore[attr-defined]
    mcp._palm_config = resolved  # type: ignore[attr-defined]
    return mcp


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


mcp = create_mcp_server()

__all__ = ["PalmRestError", "create_mcp_server", "mcp"]