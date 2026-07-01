"""Provider execution MCP tools."""

from __future__ import annotations

from typing import Any


def register_provider_tools(mcp: Any, backend: Any) -> None:
    """Register provider invoke MCP tools."""

    @mcp.tool
    def palm_providers_invoke(
        resource_ref: str,
        action: str | None = None,
        params: dict[str, Any] | None = None,
        resource_id: str | None = None,
        state: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Invoke a registered provider resource with optional params and state."""
        if resource_ref.startswith("palm://"):
            raise ValueError(
                f"{resource_ref!r} is an MCP read resource — use FetchMcpResource "
                "(read_resource), not palm_providers_invoke. For invoke, use a "
                "definition name from palm://definitions/resources."
            )
        body: dict[str, Any] = {"resource_ref": resource_ref}
        if action is not None:
            body["action"] = action
        if params is not None:
            body["params"] = params
        if resource_id is not None:
            body["resource_id"] = resource_id
        if state is not None:
            body["state"] = state
        return backend.invoke_resource(body)


__all__ = ["register_provider_tools"]