"""
Schema-aware onboarding wizard — flow-level + per-step schemas and scopes.

Demonstrates layered validation (Phases 1–3 of the 0.8 state work):

1. **Per-step schemas** — validate each answer as it is entered (e.g. age must be
   an integer ≥ 18). Bound to a named wizard step scope.
2. **Flow schema** — validate the full answers object at summary and commit.
3. **CLI coercion** — text input like ``27`` is coerced to integer before schema
   checks, so operators can type naturally in the REPL.

Resume preserves scope stack and schema metadata via ``__palm:meta`` snapshots.
"""

from __future__ import annotations

from palm.definitions import FlowDefinition, ProcessDefinition
from palm.patterns.wizard.handler import CommitResult, default_commit_registry

# Flow-level schema: validates the collected answers dict at summary/commit.
# Individual steps still have their own per-step schemas for immediate feedback.
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
                # Per-step schema: checked on every input before advancing.
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
    """Commit handler — only runs after flow schema re-validates all answers."""
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