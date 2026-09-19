"""
Authoring thin apply — file snapshot then wait (0.70.4).

A leaf commits this flow through the adapter. Present starts it by catalog
id. The resource step writes snapshot **data** (not a definition revision).
The confirm step waits until present submit.

Working names (José may rename): catalog ``authoring-apply`` and
``authoring-snapshot``. Pack id stays unnamed.

Do not copy ``design_entry``. Do not register Assist. Do not stamp
``guidance_definition_id``. Snapshot JSON is rules-as-data.
"""

from __future__ import annotations

from typing import Any

from palm.definitions import FlowDefinition, ResourceDefinition

AUTHORING_SNAPSHOT_DATA = {"note": "rules-as-data"}

AUTHORING_SNAPSHOT_RESOURCE = ResourceDefinition(
    id="authoring-snapshot",
    name="authoring-snapshot",
    provider="file",
    action="write",
    resource_id="authoring/snapshot.json",
    params={
        "format": "json",
        "content": dict(AUTHORING_SNAPSHOT_DATA),
    },
    metadata={
        "example": True,
        "description": (
            "File snapshot of apply data. Not a FlowDefinition revision."
        ),
    },
)

AUTHORING_APPLY_FLOW = FlowDefinition(
    id="authoring-apply",
    name="authoring-apply",
    pattern="wizard",
    options={
        "include_summary": False,
        "allow_backtrack": True,
        "steps": [
            {
                "slug": "snapshot",
                "title": "Snapshot",
                "step_kind": "resource",
                "resource_ref": "authoring-snapshot",
                "output_key": "snapshot",
            },
            {
                "slug": "confirm",
                "title": "Confirm",
                "prompt": (
                    "Snapshot written. Confirm to finish this apply instance."
                ),
                "field_type": "text",
            },
        ],
    },
)


def snapshot_resource_body(*, documents_root: str) -> dict[str, Any]:
    """Catalog body for ``create_resource``. Tests pin ``documents_root``."""
    body = AUTHORING_SNAPSHOT_RESOURCE.to_dict()
    params = dict(body.get("params") or {})
    params["documents_root"] = documents_root
    body["params"] = params
    return body


def register_definitions(repository: object) -> None:
    """Navigator-shaped helper. Tests prove adapter land + create_resource."""
    save_resource = getattr(repository, "save_resource", None)
    save_flow = getattr(repository, "save_flow", None)
    if callable(save_resource):
        save_resource(AUTHORING_SNAPSHOT_RESOURCE)
    if callable(save_flow):
        save_flow(AUTHORING_APPLY_FLOW)
