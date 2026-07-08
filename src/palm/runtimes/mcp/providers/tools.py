"""Provider execution MCP tools."""

from __future__ import annotations

from typing import Any

from palm.common.operator.resource_remediation import enrich_provider_result
from palm.runtimes.mcp.descriptions import tool_description

_PALM_PROVIDERS_INVOKE_DESC = tool_description(
    "palm_providers_invoke",
    "Invoke a registered resource definition by name (not palm:// URIs).",
    when="One-shot provider calls outside a wizard session.",
    examples=[
        'palm_providers_invoke(resource_ref="check-health", params={"base_url": "http://127.0.0.1:8080"})',
        'palm_providers_invoke(resource_ref="fetch-customer", action="fetch", params={"customer_id": "42", "base_url": "http://api"})',
    ],
    notes=(
        "Failures include remediation hints (e.g. missing base_url). "
        "Run palm_system_doctor() resource_preflight before first invoke."
    ),
)


def register_provider_tools(mcp: Any, backend: Any) -> None:
    """Register provider invoke MCP tools."""

    @mcp.tool(description=_PALM_PROVIDERS_INVOKE_DESC)
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
        return enrich_provider_result(backend.invoke_resource(body))


__all__ = ["register_provider_tools"]