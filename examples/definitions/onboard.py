"""
Example onboarding wizard flow and process — registered by the CLI on startup.
"""

from __future__ import annotations

from palm.definitions import FlowDefinition, ProcessDefinition

ONBOARD_FLOW = FlowDefinition(
    id="flow-onboard",
    name="onboard",
    pattern="wizard",
    options={
        "steps": [
            {
                "slug": "name",
                "title": "Your Name",
                "prompt": "What is your name?",
                "validation": [{"rule": "min_length", "params": {"min": 2}}],
            },
            {
                "slug": "role",
                "title": "Your Role",
                "prompt": "Select a role",
                "field_type": "choice",
                "choices": ["developer", "manager", "other"],
            },
            {
                "slug": "confirm",
                "title": "Confirm",
                "prompt": "Save your profile?",
                "field_type": "confirm",
            },
        ],
        "allow_backtrack": True,
    },
)

ONBOARD_PROCESS = ProcessDefinition(
    id="proc-onboard",
    name="onboarding",
    flows=[ONBOARD_FLOW],
    metadata={"example": True, "description": "Interactive onboarding wizard"},
)


def register_definitions(repository: object) -> None:
    """Persist example definitions into the given repository."""
    save_flow = getattr(repository, "save_flow", None)
    save_process = getattr(repository, "save_process", None)
    if callable(save_flow):
        save_flow(ONBOARD_FLOW)
    if callable(save_process):
        save_process(ONBOARD_PROCESS)