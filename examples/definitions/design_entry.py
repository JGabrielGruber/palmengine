"""
Palm design-entry — assist scenario shell for Design Service discovery (0.30.2).

Guides create / improve flow and propose-resource intents. Does **not** call
DesignService; agents use ``palm_design_*`` tools from assistant actions.

    palm_assist(alias="design-entry/start")
"""

from __future__ import annotations

from typing import Any

from palm.definitions import FlowDefinition, ProcessDefinition
from palm.services.assist.registry import AssistContributor, register_assist_contributor
from palm.services.assist.views import (
    DESIGN_DISCOVERY_INTENTS,
    design_discovery_actions,
    design_discovery_hint,
)

_CREATE_HINT = (
    "No business flow handoff. Use palm_design_propose_flow → impact → commit. "
    "Load palm://agent/references/design-flows. Then run with palm_flows_create_session."
)
_IMPROVE_HINT = (
    "No business flow handoff. Propose changes with palm_design_propose_flow "
    "(base body from existing flow) → impact → commit."
)
_RESOURCE_HINT = (
    "No business flow handoff. Use palm_design_propose_resource → impact → commit."
)


def enrich_design_entry(view: dict[str, Any], *, context: Any) -> dict[str, Any]:
    """Post-humanize design-entry — design CTAs only (string tool/alias refs)."""
    payload = dict(view)
    intent = getattr(context, "intent", None)
    if intent is None and getattr(context, "answers_preview", None):
        preview = context.answers_preview
        if isinstance(preview, dict) and preview.get("intent") is not None:
            intent = str(preview["intent"])

    if intent in DESIGN_DISCOVERY_INTENTS:
        hint = design_discovery_hint(str(intent))
        if hint:
            payload["hint"] = hint
        payload["actions"] = design_discovery_actions(intent=str(intent))
        # Surface name/base answer in hint when present (agent convenience only)
        preview = getattr(context, "answers_preview", None) or {}
        if isinstance(preview, dict) and preview.get("name_or_base"):
            base = preview["name_or_base"]
            payload["hint"] = (
                f"{payload.get('hint', '')} name_or_base={base!r}."
            ).strip()
    elif intent == "exit" or payload.get("status") == "complete":
        payload["hint"] = (
            str(payload.get("hint") or "")
            + " Design entry finished. Use operator-entry/start or palm_assist()."
        ).strip()
        payload["actions"] = [
            {"label": "Start operator entry", "alias": "operator-entry/start"},
        ]
    return payload


DESIGN_ENTRY_FLOW = FlowDefinition(
    id="flow-palm-design-entry",
    name="palm-design-entry",
    pattern="wizard",
    options={
        "include_summary": True,
        "allow_backtrack": True,
        "metadata": {
            "assist": {
                "scenario_id": "design-entry",
                "handoff_flows": [],
                "handoff_map": {
                    "create-flow": None,
                    "improve-flow": None,
                    "propose-resource": None,
                    "exit": None,
                },
                "handoff_none_hints": {
                    "create-flow": _CREATE_HINT,
                    "improve-flow": _IMPROVE_HINT,
                    "propose-resource": _RESOURCE_HINT,
                    "exit": "Design entry exited — no handoff.",
                },
            }
        },
        "steps": [
            {
                "slug": "intent",
                "title": "Design Intent",
                "prompt": (
                    "Design Service entry. Create a flow, improve an existing flow, "
                    "propose a resource, or exit."
                ),
                "field_type": "choice",
                "choices": [
                    "create-flow",
                    "improve-flow",
                    "propose-resource",
                    "exit",
                ],
                "params": {
                    "route_on_answer": {
                        "exit": "bye",
                        "default": "name_or_base",
                    }
                },
            },
            {
                "slug": "name_or_base",
                "title": "Name or base flow",
                "prompt": (
                    "New flow name (create), existing flow id to improve, "
                    "or resource name (propose-resource). Optional — press enter to skip."
                ),
                "field_type": "text",
                "required": False,
            },
            {
                "slug": "bye",
                "title": "Exit",
                "prompt": "Leaving design entry. Say ok or exit.",
                "field_type": "text",
                "required": False,
                "params": {
                    "complete_on": ["ok", "exit", "done", "quit", ""],
                },
            },
        ],
    },
)

DESIGN_ENTRY_PROCESS = ProcessDefinition(
    id="proc-palm-design-entry",
    name="palm-design-entry",
    flows=[DESIGN_ENTRY_FLOW],
    metadata={
        "example": True,
        "description": (
            "Assist design-entry — guided Design Service discovery "
            "(propose tools only; no catalog writes)"
        ),
    },
)


def register_definitions(repository: object) -> None:
    register_assist_contributor(
        AssistContributor(
            contributor_id="builtin-design-entry",
            scenario_id="design-entry",
            flow_id="flow-palm-design-entry",
            summary=(
                "Design entry — create/improve flow or propose resource via Design tools"
            ),
            mcp_aliases=(
                ("design-entry/start", ("assist", "scenarios", "design-entry", "start")),
                (
                    "design-entry/handoff",
                    ("assist", "session", "{session_id}", "handoff"),
                ),
            ),
            assistant_enricher=enrich_design_entry,
        )
    )
    save_flow = getattr(repository, "save_flow", None)
    save_process = getattr(repository, "save_process", None)
    if callable(save_flow):
        save_flow(DESIGN_ENTRY_FLOW)
    if callable(save_process):
        save_process(DESIGN_ENTRY_PROCESS)
