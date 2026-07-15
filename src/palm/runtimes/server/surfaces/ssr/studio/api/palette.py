"""Studio palette API — aggregated registry items for the visual builder."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from palm.common.runtimes.server.protocol import ServerRequest, ServerResponse
from palm.runtimes.server.surfaces.ssr.studio.fetch import StudioFetcher

if TYPE_CHECKING:
    from palm.runtimes.server.context import ServerContext

_STRUCTURAL_ITEMS: tuple[dict[str, Any], ...] = (
    {
        "id": "structural:action",
        "kind": "action",
        "label": "Input Step",
        "description": "Collect user input in a wizard step.",
        "draggable": True,
    },
    {
        "id": "structural:condition",
        "kind": "condition",
        "label": "Condition",
        "description": "Branch or guard on a predicate.",
        "draggable": True,
    },
)


def build_palette_payload(fetcher: StudioFetcher) -> dict[str, Any]:
    """Aggregate palette sections from Palm registries."""
    sections: list[dict[str, Any]] = [
        {
            "id": "structural",
            "label": "Nodes",
            "items": [dict(item) for item in _STRUCTURAL_ITEMS],
        },
        {
            "id": "patterns",
            "label": "Patterns",
            "items": [
                {
                    "id": f"pattern:{row['name']}",
                    "kind": "pattern",
                    "ref": row["name"],
                    "label": row["name"],
                    "description": row["summary"] or row["class"],
                    "class": row["class"],
                    "draggable": True,
                }
                for row in fetcher.list_patterns()
            ],
        },
        {
            "id": "transforms",
            "label": "Transforms",
            "items": [
                {
                    "id": f"transform:{row['name']}",
                    "kind": "transform",
                    "ref": row["name"],
                    "label": row["name"],
                    "description": row["description"],
                    "mode": row["mode"],
                    "draggable": True,
                }
                for row in fetcher.list_transforms()
            ],
        },
        {
            "id": "resources",
            "label": "Resources",
            "items": [
                {
                    "id": f"resource:{row['name']}",
                    "kind": "resource",
                    "ref": row["name"],
                    "definition_id": row["definition_id"],
                    "label": row["name"],
                    "description": row["summary"],
                    "provider": row["provider"],
                    "action": row["action"],
                    "param_keys": row["param_keys"],
                    "draggable": True,
                }
                for row in fetcher.list_resources()
            ],
        },
        {
            "id": "flows",
            "label": "Flow templates",
            "items": [
                {
                    "id": f"flow:{row['flow_id']}",
                    "kind": "flow",
                    "ref": row["flow_id"],
                    "label": row["name"],
                    "description": f"{row['pattern']} flow",
                    "pattern": row["pattern"],
                    "has_state_schema": row["has_state_schema"],
                    "draggable": False,
                }
                for row in fetcher.list_flow_templates()
            ],
        },
    ]
    return {"version": fetcher.version, "sections": sections}


def get_palette(ctx: ServerContext, request: ServerRequest) -> ServerResponse:
    """Return the Studio palette payload."""
    fetcher = StudioFetcher(ctx)
    return ServerResponse(status=200, body=build_palette_payload(fetcher))
