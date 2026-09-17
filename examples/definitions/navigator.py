"""
Navigator — operator-guidance wizard (0.69.6).

Catalog chooser beside ``operator_entry``. Names any catalog definition.
Stays ``WAITING_FOR_INPUT`` after naming work. Sibling start is the kit
(``spawn_sibling``). Return is ``focus`` of ``guidance_instance_id``.

Do not copy operator-entry handoff, ``__end__`` after intent, or Assist
scenario façade.
"""

from __future__ import annotations

from palm.definitions import FlowDefinition, ProcessDefinition

NAVIGATOR_FLOW = FlowDefinition(
    id="navigator",
    name="navigator",
    pattern="wizard",
    options={
        "include_summary": False,
        "allow_backtrack": True,
        "steps": [
            {
                "slug": "next",
                "title": "What next?",
                "prompt": (
                    "Name a catalog definition to start as a sibling. "
                    "This guidance instance stays waiting."
                ),
                "field_type": "text",
                "params": {
                    "route_on_answer": {
                        "default": "next",
                    }
                },
            },
        ],
    },
)

NAVIGATOR_PROCESS = ProcessDefinition(
    name="navigator",
    flows=[NAVIGATOR_FLOW],
    metadata={
        "example": True,
        "description": (
            "Operator-guidance chooser: stay waiting, sibling start, "
            "return is focus"
        ),
    },
)


def register_definitions(repository: object) -> None:
    save_flow = getattr(repository, "save_flow", None)
    save_process = getattr(repository, "save_process", None)
    if callable(save_flow):
        save_flow(NAVIGATOR_FLOW)
    if callable(save_process):
        save_process(NAVIGATOR_PROCESS)
