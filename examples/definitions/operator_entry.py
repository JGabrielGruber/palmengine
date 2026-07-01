"""
Palm operator entry — assist scenario for agent/human triage and handoff.

Demonstrates the 0.18 assist domain: a wizard-driven entry flow that recommends
a business flow handoff based on operator intent.

Try via assist REST::

    POST /v1/api/assist/scenarios/operator-entry/start
"""

from __future__ import annotations

from palm.definitions import FlowDefinition, ProcessDefinition
from palm.services.assist.registry import AssistContributor, register_assist_contributor

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
            ),
        )
    )
    save_flow = getattr(repository, "save_flow", None)
    save_process = getattr(repository, "save_process", None)
    if callable(save_flow):
        save_flow(OPERATOR_ENTRY_FLOW)
    if callable(save_process):
        save_process(OPERATOR_ENTRY_PROCESS)