"""
Schema-aware onboarding wizard — flow-level + per-step schemas and scopes.

Demonstrates layered validation:

- **Flow schema** — validates the full answers object at summary/commit
- **Step schemas** — validate individual inputs (age integer, role enum)

Resume preserves scope stack and schema metadata via ``__palm:meta`` snapshots.
"""

from __future__ import annotations

from palm.definitions import FlowDefinition, ProcessDefinition
from palm.patterns.wizard.handler import CommitResult, default_commit_registry

SCHEMA_WIZARD_FLOW = FlowDefinition(
    id="flow-schema-onboard",
    name="schema-onboard",
    pattern="wizard",
    state_schema={
        "type": "object",
        "properties": {
            "name": {"type": "string"},
            "age": {"type": "integer", "minimum": 18},
            "role": {"type": "string", "enum": ["developer", "manager"]},
        },
        "required": ["name", "age", "role"],
    },
    options={
        "include_summary": True,
        "include_commit": True,
        "commit_hook": "persist_schema_profile",
        "allow_backtrack": True,
        "steps": [
            {
                "slug": "name",
                "title": "Your Name",
                "prompt": "What is your name?",
                "state_schema": {"type": "string"},
                "validation": [{"rule": "min_length", "params": {"min": 2}}],
            },
            {
                "slug": "age",
                "title": "Your Age",
                "prompt": "How old are you?",
                "state_schema": {"type": "integer", "minimum": 18},
            },
            {
                "slug": "role",
                "title": "Your Role",
                "prompt": "Select a role",
                "field_type": "choice",
                "choices": ["developer", "manager"],
                "state_schema": {"type": "string", "enum": ["developer", "manager"]},
            },
        ],
    },
)

SCHEMA_WIZARD_PROCESS = ProcessDefinition(
    id="proc-schema-onboard",
    name="schema-onboarding",
    flows=[SCHEMA_WIZARD_FLOW],
    metadata={
        "example": True,
        "description": "Wizard with flow-level and per-step state schemas",
    },
)


def _persist_schema_profile(ctx: object) -> CommitResult:
    answers = getattr(ctx, "answers", {})
    profile = {
        "name": answers.get("name"),
        "age": answers.get("age"),
        "role": answers.get("role"),
    }
    if not all(profile.values()):
        return CommitResult.failure("All fields are required")
    return CommitResult.success({"profile": profile})


def register_definitions(repository: object) -> None:
    default_commit_registry().register("persist_schema_profile", _persist_schema_profile)
    save_flow = getattr(repository, "save_flow", None)
    save_process = getattr(repository, "save_process", None)
    if callable(save_flow):
        save_flow(SCHEMA_WIZARD_FLOW)
    if callable(save_process):
        save_process(SCHEMA_WIZARD_PROCESS)