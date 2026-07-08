"""
Palm operator entry — assist scenario for agent/human triage and handoff.

Demonstrates the 0.18 assist domain: a wizard-driven entry flow that recommends
a business flow handoff based on operator intent.

0.30.1 — also surfaces Design Service discovery (create/improve flow) via
choices, assistant actions, and intent-specific handoff none-hints.

Try via assist REST::

    POST /v1/api/assist/scenarios/operator-entry/start
"""

from __future__ import annotations

from typing import Any

from palm.definitions import FlowDefinition, ProcessDefinition
from palm.services.assist.registry import AssistContributor, register_assist_contributor
from palm.services.assist.views import (
    DESIGN_DISCOVERY_INTENTS,
    design_discovery_actions,
    design_discovery_hint,
    post_terminal_design_actions,
)


def enrich_operator_entry(view: dict[str, Any], *, context: Any) -> dict[str, Any]:
    """Post-humanize operator-entry turns — catalog, design CTAs, handoff hints."""
    payload = dict(view)
    step = payload.get("step_slug") or payload.get("step")
    if isinstance(step, dict):
        step = step.get("slug") or step.get("step")
    # compose.step may nest under slim compose
    compose = payload.get("compose")
    if step is None and isinstance(compose, dict):
        step = compose.get("step")
    operator_mode = payload.get("operator_mode")
    intent = getattr(context, "intent", None)
    if intent is None and getattr(context, "answers_preview", None):
        preview = context.answers_preview
        if isinstance(preview, dict) and preview.get("intent") is not None:
            intent = str(preview["intent"])

    if step == "catalog" or operator_mode == "inspect":
        payload["operator_mode"] = "inspect"
        payload["hint"] = (
            "Read-only catalog mode. Use actions to inspect flows, propose a new flow, "
            "or list waiting sessions. Say exit when done."
        )
        payload["actions"] = _catalog_actions(payload)
        mutation = payload.get("mutation")
        if isinstance(mutation, dict):
            mutation = dict(mutation)
            mutation["agent_hint"] = (
                "Inspect catalog: use read/design-discovery actions only; "
                "send exit when the user is done."
            )
            payload["mutation"] = mutation
    elif intent in DESIGN_DISCOVERY_INTENTS:
        design_hint = design_discovery_hint(str(intent))
        if design_hint:
            payload["hint"] = design_hint
        if payload.get("handoff_ready") or payload.get("status") == "complete":
            payload["actions"] = post_terminal_design_actions(intent=str(intent))
            extra = "Handoff returns kind=design — use palm_design_* tools (or re-enter via actions)."
            hint = str(payload.get("hint") or "")
            if "kind=design" not in hint.lower() and "kind: design" not in hint.lower():
                payload["hint"] = f"{hint} {extra}".strip() if hint else extra
        else:
            payload["actions"] = design_discovery_actions(intent=str(intent))
    elif payload.get("handoff_ready"):
        extra = "Say handoff to start your flow."
        hint = str(payload.get("hint") or "")
        if extra.lower() not in hint.lower():
            payload["hint"] = f"{hint} {extra}".strip() if hint else extra
    return payload


def _catalog_actions(payload: dict[str, Any]) -> list[dict[str, Any]]:
    session_id = payload.get("session_id")
    actions: list[dict[str, Any]] = [
        {
            "label": "List flows",
            "alias": "assist/catalog/flows",
        },
        {
            "label": "List waiting sessions",
            "alias": "assist/catalog/waiting",
        },
        {
            "label": "Publish new flow (one call)",
            "alias": "design/publish",
        },
        {
            "label": "Doctor (resource preflight)",
            "alias": "assist/doctor",
        },
    ]
    if session_id:
        actions.append(
            {
                "label": "Inspect this session",
                "alias": "flows/session",
                "params": {"session_id": session_id},
            }
        )
    actions.append(
        {
            "label": "Exit catalog",
            "alias": "flows/session-input",
            "params": {"session_id": session_id, "input": "exit"},
        }
    )
    return actions


_CREATE_FLOW_HINT = (
    "No business flow handoff. One call: palm_design_publish_flow(body=…)."
)
_IMPROVE_FLOW_HINT = (
    "No business flow handoff. One call: palm_design_publish_flow(base_flow_id=…, body=…)."
)

OPERATOR_ENTRY_FLOW = FlowDefinition(
    id="flow-palm-operator-entry",
    name="palm-operator-entry",
    pattern="wizard",
    options={
        "include_summary": True,
        "allow_backtrack": True,
        "metadata": {
            "assist": {
                "scenario_id": "operator-entry",
                "handoff_flows": [
                    "todo-builder",
                    "compositional-parent",
                    "coconut-npc",
                ],
                "handoff_map": {
                    "todo-builder": "todo-builder",
                    "compositional-parent": "compositional-parent",
                    "coconut-npc": "coconut-npc",
                    "inspect-only": None,
                    "create-flow": None,
                    "improve-flow": None,
                    "propose-resource": None,
                },
                "design_handoff_intents": [
                    "create-flow",
                    "improve-flow",
                    "propose-resource",
                ],
                "handoff_none_hints": {
                    "create-flow": _CREATE_FLOW_HINT,
                    "improve-flow": _IMPROVE_FLOW_HINT,
                    "propose-resource": (
                        "No business flow handoff. One call: "
                        "palm_design_publish_resource(body=…)."
                    ),
                    "inspect-only": (
                        "No business flow handoff. Catalog inspect complete."
                    ),
                },
            }
        },
        "steps": [
            {
                "slug": "intent",
                "title": "Operator Intent",
                "prompt": (
                    "What would you like to do with Palm? "
                    "Run a demo flow (todo, compositional, coconut NPC with KV resources), "
                    "design a flow/resource, or inspect the catalog."
                ),
                "field_type": "choice",
                "choices": [
                    "todo-builder",
                    "compositional-parent",
                    "coconut-npc",
                    "create-flow",
                    "improve-flow",
                    "propose-resource",
                    "inspect-only",
                ],
                "params": {
                    "route_on_answer": {
                        "inspect-only": "catalog",
                        # 0.30.5 — skip summary confirm (weak-LLM); design CTAs on complete
                        "create-flow": "__end__",
                        "improve-flow": "__end__",
                        "propose-resource": "__end__",
                        "default": "summary",
                    }
                },
            },
            {
                "slug": "catalog",
                "title": "Inspect Catalog",
                "prompt": "Read-only catalog mode. Say exit when done.",
                "field_type": "text",
                "required": False,
                "params": {
                    "inspect_only": True,
                    "complete_on": ["exit", "quit", "done"],
                },
            },
        ],
    },
)

OPERATOR_ENTRY_PROCESS = ProcessDefinition(
    id="proc-palm-operator-entry",
    name="palm-operator-entry",
    flows=[OPERATOR_ENTRY_FLOW],
    metadata={
        "example": True,
        "description": (
            "Assist operator entry — triage intent, design discovery, "
            "and hand off to business flows"
        ),
    },
)


def register_definitions(repository: object) -> None:
    register_assist_contributor(
        AssistContributor(
            contributor_id="builtin-operator-entry",
            scenario_id="operator-entry",
            flow_id="flow-palm-operator-entry",
            summary=(
                "Palm operator entry — triage intent, design discovery, "
                "and hand off to business flows"
            ),
            mcp_aliases=(
                ("operator-entry/start", ("assist", "scenarios", "operator-entry", "start")),
                (
                    "operator-entry/handoff",
                    ("assist", "session", "{session_id}", "handoff"),
                ),
                (
                    "operator-entry/inspect",
                    ("assist", "scenarios", "operator-entry", "inspect"),
                ),
            ),
            assistant_enricher=enrich_operator_entry,
        )
    )
    save_flow = getattr(repository, "save_flow", None)
    save_process = getattr(repository, "save_process", None)
    if callable(save_flow):
        save_flow(OPERATOR_ENTRY_FLOW)
    if callable(save_process):
        save_process(OPERATOR_ENTRY_PROCESS)
