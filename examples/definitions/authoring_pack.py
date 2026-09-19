"""
Authoring pack — catalog wizard present can start (0.70.3).

Asks for a shape. Stays ``WAITING_FOR_INPUT`` after submit
(``route_on_answer.default`` stays on the same step). A leaf that commits
a thin apply flow waits for 0.70.4.

Pack id stays unnamed. As-built catalog name is ``authoring-pack``.
José may rename. Spoken word ``author`` is teaching only — not this id.

Do not copy ``design_entry``. Do not register Assist. Do not stamp
``guidance_definition_id``. Proof path is adapter ``land`` / ``commit``,
not leftover ``repository.save_flow``.
"""

from __future__ import annotations

from palm.definitions import FlowDefinition, ProcessDefinition

AUTHORING_PACK_FLOW = FlowDefinition(
    id="authoring-pack",
    name="authoring-pack",
    pattern="wizard",
    options={
        "include_summary": False,
        "allow_backtrack": True,
        "steps": [
            {
                "slug": "shape",
                "title": "Shape",
                "prompt": (
                    "Submit a shape (text is enough). This authoring instance stays waiting."
                ),
                "field_type": "text",
                "params": {
                    "route_on_answer": {
                        "default": "shape",
                    }
                },
            },
        ],
    },
)

AUTHORING_PACK_PROCESS = ProcessDefinition(
    name="authoring-pack",
    flows=[AUTHORING_PACK_FLOW],
    metadata={
        "example": True,
        "description": (
            "Authoring pack wizard: stay waiting after a shape. "
            "As-built id authoring-pack; pack id unnamed"
        ),
    },
)


def register_definitions(repository: object) -> None:
    """Navigator-shaped helper. Tests prove land → present start."""
    save_flow = getattr(repository, "save_flow", None)
    save_process = getattr(repository, "save_process", None)
    if callable(save_flow):
        save_flow(AUTHORING_PACK_FLOW)
    if callable(save_process):
        save_process(AUTHORING_PACK_PROCESS)
