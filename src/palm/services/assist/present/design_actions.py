"""Design-intent CTAs and action prioritization."""

from __future__ import annotations

from typing import Any

from palm.services.assist.present.actions import merge_assistant_actions

# Intents that surface Design Service tools (0.30.1)
DESIGN_DISCOVERY_INTENTS = frozenset({"create-flow", "improve-flow", "propose-resource"})


def design_discovery_actions(
    *,
    intent: str | None = None,
    operator_mode: str | None = None,
    for_catalog: bool = False,
) -> list[dict[str, Any]]:
    """Minimal CTAs for Design tools — prefer one-shot publish (weak-LLM)."""
    actions: list[dict[str, Any]] = []
    catalog_mode = for_catalog or operator_mode == "inspect"
    if intent == "create-flow" or catalog_mode:
        actions.append(
            {
                "label": "Publish new flow (one call)",
                "tool": "palm_design_publish_flow",
            }
        )
    if intent == "improve-flow":
        actions.append(
            {
                "label": "Publish flow change (one call)",
                "tool": "palm_design_publish_flow",
            }
        )
    if intent == "propose-resource" or catalog_mode:
        actions.append(
            {
                "label": "Publish resource (one call)",
                "tool": "palm_design_publish_resource",
            }
        )
    return merge_assistant_actions(actions)


def design_discovery_hint(intent: str | None) -> str:
    """Short hint — avoid multi-tool scripts (weak-LLM token budget)."""
    if intent == "create-flow":
        return (
            "One call: palm_design_publish_flow(body={name, pattern, options.steps}). "
            "Handoff optional."
        )
    if intent == "improve-flow":
        return (
            "One call: palm_design_publish_flow(base_flow_id=…, body=…). "
            "Handoff optional."
        )
    if intent == "propose-resource":
        return (
            "One call: palm_design_publish_resource(body={name, provider, action, …}). "
            "Flows like coconut-npc need kv resources registered first."
        )
    return ""


def post_terminal_design_actions(
    *,
    intent: str | None = None,
    name_or_base: str | None = None,
) -> list[dict[str, Any]]:
    """Compact re-entry CTAs after design work — design first, few session verbs."""
    actions: list[dict[str, Any]] = list(
        design_discovery_actions(intent=intent or "create-flow")
    )
    actions.append({"label": "Start operator entry", "alias": "operator-entry/start"})
    if name_or_base and intent in {"create-flow", "improve-flow"}:
        actions.append(
            {
                "label": f"Run flow {name_or_base}",
                "tool": "palm_flows_create_session",
                "params": {"flow_id": name_or_base},
            }
        )
    return merge_assistant_actions(actions)


def prioritize_assistant_actions_for_design(
    actions: list[dict[str, Any]],
    *,
    intent: str | None,
    handoff_ready: bool = False,
    waiting_for_input: bool = False,
) -> list[dict[str, Any]]:
    """Put design tools first; drop noisy session verbs for design intents (0.30.4)."""
    if intent not in DESIGN_DISCOVERY_INTENTS:
        return actions

    design_first: list[dict[str, Any]] = []
    session_keep: list[dict[str, Any]] = []
    other: list[dict[str, Any]] = []

    for action in actions:
        if not isinstance(action, dict):
            continue
        tool = str(action.get("tool") or "")
        alias = str(action.get("alias") or "")
        label = str(action.get("label") or "")
        if tool.startswith("palm_design") or alias.startswith("design/"):
            design_first.append(action)
            continue
        if label == "Send answer" and waiting_for_input:
            session_keep.append(action)
            continue
        if "Hand off" in label and handoff_ready:
            session_keep.append(action)
            continue
        if label == "Cancel session":
            session_keep.append(action)
            continue
        if alias in {"operator-entry/start", "design-entry/start"}:
            other.append(action)
            continue
        if tool == "palm_flows_create_session":
            other.append(action)
            continue
        continue

    return merge_assistant_actions(design_first, session_keep, other)


__all__ = [
    "DESIGN_DISCOVERY_INTENTS",
    "design_discovery_actions",
    "design_discovery_hint",
    "post_terminal_design_actions",
    "prioritize_assistant_actions_for_design",
]
