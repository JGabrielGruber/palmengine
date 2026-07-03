"""
Palm operator entry — assist scenario for agent/human triage and handoff.

Demonstrates the 0.18 assist domain: a wizard-driven entry flow that recommends
a business flow handoff based on operator intent.

Try via assist REST::

    POST /v1/api/assist/scenarios/operator-entry/start
"""

from __future__ import annotations

from typing import Any

from palm.definitions import FlowDefinition, ProcessDefinition
from palm.services.assist.registry import AssistContributor, register_assist_contributor


def enrich_operator_entry(view: dict[str, Any], *, context: Any) -> dict[str, Any]:
    """Post-humanize operator-entry turns — catalog read mode and handoff CTAs."""
    payload = dict(view)
    step = payload.get("step_slug") or payload.get("step")
    operator_mode = payload.get("operator_mode")
    if step == "catalog" or operator_mode == "inspect":
        payload["operator_mode"] = "inspect"
        payload["hint"] = (
            "Read-only catalog mode. Use actions to inspect flows and waiting sessions. "
            "Say exit when done."
        )
        payload["actions"] = _catalog_actions(payload)
        mutation = payload.get("mutation")
        if isinstance(mutation, dict):
            mutation = dict(mutation)
            mutation["agent_hint"] = (
                "Inspect catalog: use read actions only; send exit when the user is done."
            )
            payload["mutation"] = mutation
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
            "tool": "palm_system_list_waiting",
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
                "handoff_flows": ["todo-builder", "compositional-parent"],
                "handoff_map": {
                    "todo-builder": "todo-builder",
                    "compositional-parent": "compositional-parent",
                    "inspect-only": None,
                },
            }
        },
        "steps": [
            {
                "slug": "intent",
                "title": "Operator Intent",
                "prompt": "What would you like to do with Palm?",
                "field_type": "choice",
                "choices": ["todo-builder", "compositional-parent", "inspect-only"],
                "params": {
                    "route_on_answer": {
                        "inspect-only": "catalog",
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
        "description": "Assist operator entry — triage and handoff to business flows",
    },
)


def register_definitions(repository: object) -> None:
    register_assist_contributor(
        AssistContributor(
            contributor_id="builtin-operator-entry",
            scenario_id="operator-entry",
            flow_id="flow-palm-operator-entry",
            summary="Palm operator entry — triage intent and hand off to business flows",
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