"""Wizard pattern MCP tools — collection actions and commit preview."""

from __future__ import annotations

from typing import Any

from palm.common.operator.collection_drive import drive_collection_add
from palm.common.operator.collection_input import resolve_wizard_collection_action
from palm.common.operator.commit_preview import wizard_commit_preview
from palm.common.operator.compact import compact_wizard_inspect
from palm.common.operator.flow_session_view import shape_flow_session_view
from palm.common.operator.view_registry import normalize_view_format


def register_wizard_mcp_tools(mcp: Any, rest_client: Any) -> None:
    """Register wizard-specific MCP tools on ``mcp``."""

    @mcp.tool
    def palm_wizard_collection_action(
        instance_id: str,
        action: str,
        item_index: int | None = None,
        value: Any = None,
        format: str = "powertool",
    ) -> dict[str, Any]:
        """Drive a wizard collection step: add, edit, remove, done, cancel, confirm_remove."""
        wizard_view = rest_client.get_wizard(instance_id)
        prompt = wizard_view.get("prompt") or {}
        flow_id = wizard_view.get("flow_name") or wizard_view.get("flow")
        normalized_action = str(action or "").strip().lower()

        def _shape_payload(view: dict[str, Any]) -> dict[str, Any]:
            if normalize_view_format(format) == "assistant":
                invoke_tree = None
                if hasattr(rest_client, "get_instance_tree"):
                    invoke_tree = rest_client.get_instance_tree(instance_id)
                payload = shape_flow_session_view(
                    view,
                    format=format,
                    session_id=instance_id,
                    flow_id=str(flow_id) if flow_id is not None else None,
                    invoke_tree=invoke_tree,
                )
            else:
                payload = compact_wizard_inspect(view)
            payload["collection_action"] = action
            return payload

        if normalized_action == "add" and value is not None:
            if prompt.get("collection_phase") == "field":
                raise ValueError(
                    "'add' is a menu-phase collection action; "
                    "provide field values via palm_wizard_input(input=…)"
                )
            view = drive_collection_add(
                lambda resolved: rest_client.provide_wizard_input(instance_id, resolved),
                value=value,
                wizard_view=wizard_view,
            )
            return _shape_payload(view)
        resolved = resolve_wizard_collection_action(
            action,
            item_index=item_index,
            value=value,
            wizard_view=wizard_view,
        )
        if resolved == "" and value is None:
            raise ValueError(
                "collection action requires value for field input, or a recognized action name"
            )
        view = rest_client.provide_wizard_input(instance_id, resolved)
        return _shape_payload(view)

    @mcp.tool
    def palm_wizard_commit_preview(instance_id: str) -> dict[str, Any]:
        """Preview answers and commit hook payload before confirming commit."""
        wizard_view = rest_client.get_wizard(instance_id)
        return wizard_commit_preview(wizard_view)


__all__ = ["register_wizard_mcp_tools"]
