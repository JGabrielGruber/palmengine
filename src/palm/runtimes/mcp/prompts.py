"""Core MCP prompt templates for Palm operator workflows."""

from __future__ import annotations

import json
from typing import Any


def register_core_prompts(mcp: Any, config: Any, rest_client: Any) -> None:
    """Register operator prompt templates on ``mcp``."""

    @mcp.prompt("debug-wizard-block")
    def debug_wizard_block(instance_id: str) -> str:
        """Find blockers for a waiting wizard (validation, child wait, collection)."""
        return (
            f"Debug Palm wizard instance {instance_id}.\n\n"
            "1. Call palm_inspect_instance with format=compact.\n"
            "2. If validation_error is set, fix input and retry palm_wizard_input "
            "(use plain input strings: yes/no, choice slugs, text—not JSON).\n"
            "3. If waiting_for_child is true, call palm_resume_child_wait or inspect the child.\n"
            "4. If collection_phase is menu, use palm_wizard_collection_action; "
            "if field/select_item/remove_confirm, use palm_wizard_input(input=…).\n"
            "5. Read palm://instances/{instance_id}/tree for compositional parent/child context.\n"
            f"REST base: {config.base_url}"
        )

    @mcp.prompt("drive-wizard-to-step")
    def drive_wizard_to_step(instance_id: str, target_step: str) -> str:
        """Advance a wizard toward target_step with minimal inputs."""
        return (
            f"Drive Palm wizard {instance_id} toward step {target_step!r}.\n\n"
            "Loop: palm_inspect_instance → palm_wizard_input(input=…) for fields; "
            "palm_wizard_collection_action for collection menu phase only → re-inspect until "
            "current step matches target "
            "or the wizard completes. Use palm_wizard_backtrack only when the operator asks."
        )

    @mcp.prompt("explain-compositional-stack")
    def explain_compositional_stack(instance_id: str) -> str:
        """Summarize parent/child invoke stack and recommended next action."""
        tree = rest_client.get_instance_tree(instance_id)
        return (
            f"Explain the compositional invoke stack for Palm instance {instance_id}.\n\n"
            f"Invoke tree JSON:\n{json.dumps(tree, indent=2)}\n\n"
            "Summarize root flow, active child (if any), and the single best next operator action."
        )

    @mcp.prompt("operator-handoff")
    def operator_handoff(instance_id: str) -> str:
        """Human-readable handoff summary with Explorer links."""
        wizard = rest_client.get_wizard(instance_id)
        flow = wizard.get("flow_name") or "unknown"
        step = wizard.get("current_step_slug") or "unknown"
        status = wizard.get("status") or "unknown"
        base = str(config.base_url).rstrip("/")
        return (
            f"Palm wizard handoff — instance {instance_id}\n"
            f"Flow: {flow}\n"
            f"Step: {step}\n"
            f"Status: {status}\n"
            f"Explorer: {base}/explorer/instances/{instance_id}\n"
            f"REST: {base}/v1/wizards/{instance_id}\n"
            "Write a concise human summary and the next action for the operator."
        )


__all__ = ["register_core_prompts"]
