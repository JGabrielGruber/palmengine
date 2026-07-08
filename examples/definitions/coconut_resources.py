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


def _register_coconut_transforms() -> None:
    """Load transforms whether this module is imported or bootstrap file-loaded."""
    register_fn = None
    try:
        from examples.definitions.coconut_transforms import register_coconut_transforms

        register_fn = register_coconut_transforms
    except ModuleNotFoundError:
        import importlib.util
        from pathlib import Path

        path = Path(__file__).resolve().parent / "coconut_transforms.py"
        spec = importlib.util.spec_from_file_location("_palm_coconut_transforms", path)
        if spec is None or spec.loader is None:
            raise ImportError(f"cannot load coconut transforms from {path}") from None
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        register_fn = getattr(module, "register_coconut_transforms", None)
        if not callable(register_fn):
            raise ImportError("coconut_transforms missing register_coconut_transforms") from None

    register_fn()


def register_definitions(repository: object) -> None:
    _register_coconut_transforms()
    save_resource = getattr(repository, "save_resource", None)
    if callable(save_resource):
        save_resource(LOAD_COCONUT_PLAYER)
        save_resource(SAVE_COCONUT_PLAYER)


__all__ = [
    "LOAD_COCONUT_PLAYER",
    "SAVE_COCONUT_PLAYER",
    "register_definitions",
]