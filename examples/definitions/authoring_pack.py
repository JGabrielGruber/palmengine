"""
Authoring pack — catalog wizard present can start (0.70.3 / 0.70.5).

Asks for a shape (catalog mapping: flow or resource). A resource step walks
the authoring adapter (``authoring-commit``). Pack id stays unnamed. As-built
catalog name is ``authoring-pack``. José may rename.

Do not copy ``design_entry``. Do not register Assist. Do not stamp
``guidance_definition_id``. Proof path is adapter ``land`` / ``commit``,
not leftover ``repository.save_flow``.
"""

from __future__ import annotations

from palm.definitions import FlowDefinition, ProcessDefinition, ResourceDefinition

AUTHORING_COMMIT_RESOURCE = ResourceDefinition(
    id="authoring-commit",
    name="authoring-commit",
    provider="authoring",
    action="commit",
    params={"body": "{{ state.shape }}"},
    metadata={
        "example": True,
        "description": (
            "Job leaf: walk palm.kits.authoring commit with the submitted shape. "
            "Working name authoring-commit; provider name authoring unnamed"
        ),
    },
)

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
                "prompt": "Submit a shape (catalog mapping).",
                "field_type": "text",
            },
            {
                "slug": "publish",
                "title": "Publish",
                "step_kind": "resource",
                "resource_ref": "authoring-commit",
                "output_key": "published",
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
            "Authoring pack wizard: submit a shape; a resource leaf commits it. "
            "As-built id authoring-pack; pack id unnamed"
        ),
    },
)


def register_definitions(repository: object) -> None:
    """Navigator-shaped helper. Tests prove land → present start."""
    save_resource = getattr(repository, "save_resource", None)
    save_flow = getattr(repository, "save_flow", None)
    save_process = getattr(repository, "save_process", None)
    if callable(save_resource):
        save_resource(AUTHORING_COMMIT_RESOURCE)
    if callable(save_flow):
        save_flow(AUTHORING_PACK_FLOW)
    if callable(save_process):
        save_process(AUTHORING_PACK_PROCESS)
