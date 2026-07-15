"""
Coconut profile prep — pipeline slice mirroring wizard transform steps.

Non-interactive alternative to ``load_player`` → ``mark_returning`` → ``returning_note``
transform chain in :mod:`coconut.npc`. Seed ``player_profile`` (+ ``player_name``) via
``SubmitFlowCommand.state`` or static ``initial_state``.
"""

from __future__ import annotations

from palm.definitions import FlowDefinition, ProcessDefinition

COCONUT_PROFILE_PIPELINE = FlowDefinition(
    id="flow-coconut-profile-pipeline",
    name="coconut-profile-pipeline",
    pattern="pipeline",
    options={
        "initial_state": {
            "player_profile": {"visit_count": 0},
            "player_name": "Traveler",
        },
        "steps": [
            {
                "name": "stamp_player_name",
                "source_key": "player_profile",
                "target_key": "player_profile",
                "rule": "jsonpath_set",
                "options": {
                    "path": "player_name",
                    "set_value_from_key": "player_name",
                },
            },
            {
                "name": "mark_returning",
                "source_key": "player_profile",
                "target_key": "is_returning",
                "rule": "conditional",
                "options": {
                    "field": "visit_count",
                    "gt": 0,
                    "then": True,
                    "else": False,
                },
            },
            {
                "name": "returning_note",
                "source_key": "is_returning",
                "target_key": "returning_note",
                "rule": "conditional",
                "options": {
                    "is_truthy": True,
                    "then": " I remember you.",
                    "else": "",
                },
            },
            {
                "name": "merge_returning_note",
                "source_key": "player_profile",
                "target_key": "player_profile",
                "rule": "jsonpath_set",
                "options": {
                    "path": "returning_note",
                    "set_value_from_key": "returning_note",
                },
            },
        ],
    },
)

COCONUT_PROFILE_PIPELINE_PROCESS = ProcessDefinition(
    id="proc-coconut-profile-pipeline",
    name="coconut-profile-pipeline",
    flows=[COCONUT_PROFILE_PIPELINE],
    metadata={"example": True},
)


def register_definitions(repository: object) -> None:
    save_flow = getattr(repository, "save_flow", None)
    save_process = getattr(repository, "save_process", None)
    if callable(save_flow):
        save_flow(COCONUT_PROFILE_PIPELINE)
    if callable(save_process):
        save_process(COCONUT_PROFILE_PIPELINE_PROCESS)


__all__ = [
    "COCONUT_PROFILE_PIPELINE",
    "COCONUT_PROFILE_PIPELINE_PROCESS",
    "register_definitions",
]