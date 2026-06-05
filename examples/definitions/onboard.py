"""
Onboarding wizard — validation, summary, and transactional commit.

Demonstrates a realistic user onboarding flow with persisted definitions
and a named commit handler registered at import time.
"""

from __future__ import annotations

from typing import Any

from palm.definitions import FlowDefinition, ProcessDefinition
from palm.patterns.wizard.commit import CommitResult, default_commit_registry

ONBOARD_FLOW = FlowDefinition(
    id="flow-onboard",
    name="onboard",
    pattern="wizard",
    options={
        "include_summary": True,
        "include_commit": True,
        "commit_hook": "persist_profile",
        "allow_backtrack": True,
        "steps": [
            {
                "slug": "name",
                "title": "Your Name",
                "prompt": "What is your name?",
                "validation": [{"rule": "min_length", "params": {"min": 2}}],
            },
            {
                "slug": "email",
                "title": "Work Email",
                "prompt": "Enter your work email",
                "validation": [
                    {
                        "rule": "regex",
                        "params": {
                            "pattern": r"^[^@\s]+@[^@\s]+\.[^@\s]+$",
                            "message": "Enter a valid email address",
                        },
                    }
                ],
            },
            {
                "slug": "role",
                "title": "Your Role",
                "prompt": "Select a role",
                "field_type": "choice",
                "choices": ["developer", "manager", "other"],
            },
        ],
    },
)

ONBOARD_PROCESS = ProcessDefinition(
    id="proc-onboard",
    name="onboarding",
    flows=[ONBOARD_FLOW],
    metadata={
        "example": True,
        "description": "Interactive onboarding with summary + commit",
    },
)


def _persist_profile(ctx: Any) -> CommitResult:
    profile = {
        "name": ctx.answers.get("name"),
        "email": ctx.answers.get("email"),
        "role": ctx.answers.get("role"),
    }
    if not profile["name"] or not profile["email"]:
        return CommitResult.failure("Name and email are required to commit")
    return CommitResult.success({"profile": profile, "stored": True})


def register_definitions(repository: object) -> None:
    default_commit_registry().register("persist_profile", _persist_profile)
    save_flow = getattr(repository, "save_flow", None)
    save_process = getattr(repository, "save_process", None)
    if callable(save_flow):
        save_flow(ONBOARD_FLOW)
    if callable(save_process):
        save_process(ONBOARD_PROCESS)
