"""FastMCP server — Palm operator tools and resources over REST."""

from __future__ import annotations

import json
from typing import Any

from palm.common.operator.compact import compact_wizard_inspect
from palm.runtimes.mcp.config import PalmMcpConfig
from palm.runtimes.mcp.rest_client import PalmRestClient, PalmRestError

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