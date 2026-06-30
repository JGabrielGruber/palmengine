"""Studio extension metadata — registry-driven hooks for custom node types."""

from __future__ import annotations

from palm.common.runtimes.server.protocol import ServerResponse

_BUILTIN_EVENTS = (
    "canvas:node:added",
    "canvas:node:removed",
    "canvas:edge:added",
    "canvas:layout:applied",
    "canvas:group:created",
    "project:saved",
    "project:switched",
    "simulate:started",
    "simulate:completed",
    "plugin:registered",
)


def get_extensions(request: object) -> ServerResponse:
    """Expose Studio extension points for registry-driven plugins."""
    return ServerResponse(
        status=200,
        body={
            "events": list(_BUILTIN_EVENTS),
            "node_type_kinds": [
                "action",
                "condition",
                "resource",
                "transform",
                "pattern",
                "flow",
            ],
            "plugin_contract": {
                "register": "studioPlugins.register({ id, name, nodeTypes, paletteSections })",
                "events": "studioEvents.on(event, handler)",
            },
        },
    )
