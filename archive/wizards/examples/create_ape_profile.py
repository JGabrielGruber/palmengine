"""
Example Wizard: Create APE Profile

Demonstrates the full Palm wizard lifecycle:
  Introduction (explicit confirm) → ask_name → ask_age → summary → commit

This wizard is intentionally simple yet complete enough to exercise:
- RichContext generation
- Validation rules
- Custom validators
- Backtracking by slug
- Final transactional commit step
"""

from __future__ import annotations

from typing import Any

from palm.cli.solid.legacy.models.common import ValidationRule
from palm.cli.solid.legacy.models.step import StepDefinition
from palm.cli.solid.legacy.wizard.definition import WizardDefinition


def create_ape_profile_wizard() -> WizardDefinition:
    """Factory that returns a fully configured APE Profile wizard."""

    steps = [
        # ------------------------------------------------------------------
        # 1. INTRODUCTION - Always first, never backtrackable
        # ------------------------------------------------------------------
        StepDefinition(
            slug="introduction",
            type="introduction",
            title="Welcome to APE Profile Creator",
            prompt="This wizard will help you create a new APE (Ape Profile Entity) profile.",
            guidelines=(
                "You will be asked for your name and age. "
                "All information is stored only for the duration of this session.\n\n"
                "Type 'confirm' or 'yes' to begin."
            ),
            is_backtrackable=False,  # Enforced by engine anyway
            validation_rules=[],
        ),
        # ------------------------------------------------------------------
        # 2. NAME
        # ------------------------------------------------------------------
        StepDefinition(
            slug="ask_name",
            type="user_input",
            title="What is your name?",
            prompt="Please enter your full name:",
            guidelines="Use your real name or a handle you want associated with this profile.",
            validation_rules=[
                ValidationRule(type="required"),
                ValidationRule(type="min_length", params={"value": 2}),
                ValidationRule(type="max_length", params={"value": 60}),
            ],
            input_schema={"type": "string"},
        ),
        # ------------------------------------------------------------------
        # 3. AGE (uses the registered custom validator "min_age_13")
        # ------------------------------------------------------------------
        StepDefinition(
            slug="ask_age",
            type="user_input",
            title="How old are you?",
            prompt="Enter your age in years:",
            guidelines="You must be at least 13 years old to create a profile.",
            validation_rules=[
                ValidationRule(type="required"),
                ValidationRule(type="min_value", params={"value": 0}),
                ValidationRule(type="max_value", params={"value": 150}),
                ValidationRule(
                    type="custom",
                    params={"name": "min_age_13"},
                    error_message="You must be at least 13 years old.",
                ),
            ],
            input_schema={"type": "integer"},
        ),
        # ------------------------------------------------------------------
        # 4. SUMMARY - Review before commit
        # ------------------------------------------------------------------
        StepDefinition(
            slug="summary",
            type="summary",
            title="Review Your Profile",
            prompt="Please review the information below before we create your profile.",
            guidelines="If anything looks wrong, use the 'back' command to correct it.",
            # No validation rules — the engine will present collected_data nicely
        ),
        # ------------------------------------------------------------------
        # 5. COMMIT - The transactional boundary
        # ------------------------------------------------------------------
        StepDefinition(
            slug="commit",
            type="commit",
            title="Create Profile",
            prompt="Ready to create your APE profile?",
            guidelines="This is the final step. Once committed, the profile will be recorded.",
            is_backtrackable=False,
        ),
    ]

    return WizardDefinition(
        id="create_ape_profile",
        name="Create APE Profile",
        description="Interactive wizard that collects basic information and performs a transactional commit.",
        version="1.0.0",
        steps=steps,
        on_commit_hook="create_ape_profile_commit",
        metadata={
            "category": "examples",
            "tags": ["profile", "onboarding"],
            "author": "Palm Team",
        },
    )


# ----------------------------------------------------------------------
# Commit handler (registered with the engine at runtime or via registry)
# ----------------------------------------------------------------------


def ape_profile_commit_handler(session: Any) -> dict[str, Any]:
    """
    Example transactional commit handler.

    In a real application this would:
    - Write to an external system (DB, API)
    - Be idempotent
    - Return durable result
    """
    data = session.collected_data
    name = data.get("ask_name", "Unknown")
    age = data.get("ask_age", "?")

    # Simulate real work
    profile_id = f"ape_{name.lower().replace(' ', '_')[:20]}_{age}"

    return {
        "profile_id": profile_id,
        "name": name,
        "age": age,
        "status": "created",
        "message": f"APE Profile '{profile_id}' has been successfully created. Welcome, {name}!",
    }


# Convenience: allow the CLI to discover and pre-register the handler if desired
COMMIT_HANDLERS = {
    "create_ape_profile_commit": ape_profile_commit_handler,
}
