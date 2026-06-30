"""Phase 5 MCP tools — resource invoke and compositional session status."""

from __future__ import annotations

from typing import Any

from palm.common.operator.compose_status import build_compose_status


def register_phase5_tools(mcp: Any, rest_client: Any) -> None:
    """Register Phase 5 resource and compositional status tools."""

    @mcp.tool
    def palm_invoke_resource(
        resource_ref: str,
        action: str | None = None,
        params: dict[str, Any] | None = None,
        resource_id: str | None = None,
        state: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Invoke a registered resource definition with optional params and state."""
        if resource_ref.startswith("palm://"):
            raise ValueError(
                f"{resource_ref!r} is an MCP read resource — use FetchMcpResource "
                "(read_resource), not palm_invoke_resource. For invoke, use a "
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
        return rest_client.invoke_resource(body)

    @mcp.tool
    def palm_compose_status(instance_id: str) -> dict[str, Any]:
        """Compositional session summary: invoke stack, step, answers, and operator_hint."""
        tree = rest_client.get_instance_tree(instance_id)
        view = rest_client.get_wizard(instance_id)
        from palm.common.operator.compact import compact_wizard_inspect

        inspect = compact_wizard_inspect(view, include_operator_hint=False)
        return build_compose_status(tree, inspect)


__all__ = ["register_phase5_tools"]
