"""Core MCP prompt templates for Palm operator workflows."""

from __future__ import annotations

from typing import Any


def register_core_prompts(mcp: Any, config: Any, rest_client: Any) -> None:
    """Register operator prompt templates."""

    @mcp.prompt("debug-wizard-block")
    def debug_wizard_block(instance_id: str) -> str:
        return (
            "Debug a blocked wizard session.\n"
            "1. Call palm_flows_session with format=compact.\n"
            "2. If validation_error is set, fix input and retry palm_flows_session_input "
            "(plain string input=…).\n"
            "3. If waiting_for_child, read palm://instances/{id}/tree and "
            "palm_flows_session_resume_child_wait.\n"
            "4. If collection_phase is menu, use palm_wizard_collection_action; "
            "if field/select_item/remove_confirm, use palm_flows_session_input(input=…).\n"
            f"Session: {instance_id}"
        )

    @mcp.prompt("drive-wizard-to-step")
    def drive_wizard_to_step(instance_id: str, target_step: str) -> str:
        return (
            f"Drive session {instance_id} toward step {target_step!r}.\n"
            "Loop: palm_flows_session → palm_flows_session_input(input=…) for fields; "
            "palm_wizard_collection_action for collection menu phase only → re-inspect until "
            f"current_step_slug is {target_step!r} "
            "or the wizard completes. Use palm_flows_session_backtrack only when the operator asks."
        )

    @mcp.prompt("explain-compositional-stack")
    def explain_compositional_stack(instance_id: str) -> str:
        tree = rest_client.get_instance_tree(instance_id)
        return (
            f"Compositional invoke stack for {instance_id}:\n"
            f"{tree}\n"
            "Use palm_flows_compose_status for operator-oriented summary."
        )

    @mcp.prompt("operator-handoff")
    def operator_handoff(instance_id: str) -> str:
        base = rest_client.base_url.rstrip("/")
        return (
            f"Handoff for session {instance_id}.\n"
            f"Explorer: {base}/explorer/instances/{instance_id}\n"
            "Primary tools: palm_flows_session, palm_flows_session_input, "
            "palm_flows_session_resume_child_wait."
        )


__all__ = ["register_core_prompts"]