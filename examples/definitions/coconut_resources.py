"""
Coconut NPC resource definitions — local KV persistence (0.28+).

Cross-session player profiles keyed by ``player_name``. Wired into
``coconut-npc`` flow in 0.28.2; definitions register here for design/invoke.
"""

from __future__ import annotations

from palm.definitions import ResourceDefinition

LOAD_COCONUT_PLAYER = ResourceDefinition(
    id="resource-load-coconut-player",
    name="load-coconut-player",
    provider="kv",
    action="get",
    resource_id="players/{{ state.player_name }}",
    params={
        "namespace": "coconut",
        "backend": "auto",
        "default": {},
    },
    output_key="player_profile",
    metadata={
        "description": "Load cross-session coconut player profile by player_name",
        "tags": ["coconut", "kv", "read"],
    },
)

SAVE_COCONUT_PLAYER = ResourceDefinition(
    id="resource-save-coconut-player",
    name="save-coconut-player",
    provider="kv",
    action="put",
    resource_id="players/{{ state.player_name }}",
    params={
        "namespace": "coconut",
        "backend": "auto",
        "value": "{{ state.player_profile }}",
    },
    metadata={
        "description": "Persist coconut player profile keyed by player_name",
        "tags": ["coconut", "kv", "write"],
    },
)


def register_definitions(repository: object) -> None:
    save_resource = getattr(repository, "save_resource", None)
    if callable(save_resource):
        save_resource(LOAD_COCONUT_PLAYER)
        save_resource(SAVE_COCONUT_PLAYER)


__all__ = [
    "LOAD_COCONUT_PLAYER",
    "SAVE_COCONUT_PLAYER",
    "register_definitions",
]