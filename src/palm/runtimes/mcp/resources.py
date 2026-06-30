"""Core MCP resources — read-only operator catalogs and guides."""

from __future__ import annotations

import json
from typing import Any


def register_core_resources(mcp: Any, rest_client: Any, *, config: Any) -> None:
    """Register Phase 1-2b MCP resources."""

    @mcp.resource(
        "palm://agent/guide",
        mime_type="text/plain",
        annotations={"readOnlyHint": True, "idempotentHint": True},
    )
    def agent_guide() -> str:
        """Palm agent guide — llms.txt and operator protocol."""
        if config.llms_txt_path is not None:
            return config.llms_txt_path.read_text(encoding="utf-8")
        return (
            "Palm operator MCP adapter.\n"
            f"REST base: {config.base_url}\n"
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


__all__ = ["register_core_resources"]
