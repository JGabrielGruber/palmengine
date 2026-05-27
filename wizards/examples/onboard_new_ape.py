"""
Palm 0.2.1 Hierarchical Example: Onboard New APE

This wizard demonstrates the key 0.2.1 hierarchical features in a clean,
well-commented way:

- A SEQUENCE composite ("personal_section") containing child steps
- A dynamic ContextBuilder on one step (changes messaging based on collected data)
- A CONDITION node that branches execution ("age_gate")
- Full cross-level backtracking support using both simple slugs and dotted paths
- Proper summary → commit flow at the end

Run this with the Solid CLI to see breadcrumbs, dynamic guidance, and
hierarchical backtracking in action.
"""

from __future__ import annotations

from typing import Any

from palm.core.wizard.definition import WizardDefinition
from palm.models.common import StepType
from palm.models.step import StepDefinition


def onboard_new_ape_wizard() -> WizardDefinition:
    """Returns a rich hierarchical onboarding wizard."""

    # ------------------------------------------------------------------
    # Children of the "personal_section" SEQUENCE composite
    # ------------------------------------------------------------------
    personal_children = [
        StepDefinition(
            slug="ask_name",
            type=StepType.USER_INPUT,
            title="Name",
            prompt="What is your name?",
            guidelines="This will be used for your APE badge.",
            validation_rules=[{"type": "required"}, {"type": "min_length", "params": {"value": 2}}],
        ),
        StepDefinition(
            slug="ask_age",
            type=StepType.USER_INPUT,
            title="Age",
            prompt="How old are you?",
            guidelines="Must be 13 or older.",
            validation_rules=[{"type": "required"}, {"type": "min_value", "params": {"value": 13}}],
            input_schema={"type": "integer"},
        ),
    ]

    # Dynamic ContextBuilder example attached to ask_age
    def dynamic_age_guidance(data: dict[str, Any], step: StepDefinition) -> dict[str, Any]:
        age = data.get("ask_age")
        if isinstance(age, (int, float)):
            if age >= 65:
                return {
                    "guidelines": "Senior APEs receive priority access to the canopy lounge.",
                    "suggested_input": "confirm",
                }
            if age < 18:
                return {
                    "guidelines": "Minors will be paired with a mentor ape.",
                    "suggested_input": "ok",
                }
        return {"guidelines": "Standard onboarding continues."}

    personal_children[1].context_builder = dynamic_age_guidance

    # ------------------------------------------------------------------
    # CONDITION node: age_gate
    # ------------------------------------------------------------------
    adult_branch = StepDefinition(
        slug="ask_employee_id",
        type=StepType.USER_INPUT,
        title="Employee ID",
        prompt="Please enter your employee ID:",
        guidelines="Required for adults.",
        validation_rules=[{"type": "required"}],
    )

    minor_branch = StepDefinition(
        slug="ask_guardian_contact",
        type=StepType.USER_INPUT,
        title="Guardian Contact",
        prompt="Please provide a guardian's email or phone:",
        guidelines="Required for minors.",
        validation_rules=[{"type": "required"}],
    )

    age_gate = StepDefinition(
        slug="age_gate",
        type=StepType.CONDITION,
        title="Age Gate",
        prompt="Evaluating age...",
        # 0.2.2: Explicit branching rule
        # children[0] = True branch (adult), children[1] = False branch (minor)
        condition=lambda data: (data.get("ask_age") or 0) >= 18,
        children=[adult_branch, minor_branch],
    )

    # ------------------------------------------------------------------
    # Top-level steps
    # ------------------------------------------------------------------
    steps = [
        StepDefinition(
            slug="introduction",
            type=StepType.INTRODUCTION,
            title="Welcome to the APE Enclosure",
            prompt="We are excited to onboard you as a new APE!",
            guidelines="Type 'confirm' to start the structured onboarding process.",
            is_backtrackable=False,
        ),
        # Hierarchical container (the star of this example)
        StepDefinition(
            slug="personal_section",
            type=StepType.SEQUENCE,
            title="Personal Information",
            prompt="Please provide some basic details.",
            guidelines="This is a composite step containing multiple sub-steps.",
            children=personal_children,
        ),
        # The branching CONDITION
        age_gate,
        StepDefinition(
            slug="summary",
            type=StepType.SUMMARY,
            title="Onboarding Summary",
            prompt="Review your answers before finalizing.",
            guidelines="You can backtrack with simple slugs (back ask_name) or dotted paths (back personal_section.ask_age).",
        ),
        StepDefinition(
            slug="commit",
            type=StepType.COMMIT,
            title="Complete Onboarding",
            prompt="Ready to finalize your APE onboarding?",
            guidelines="This step is transactional.",
            is_backtrackable=False,
        ),
    ]

    return WizardDefinition(
        id="onboard_new_ape",
        name="Onboard New APE",
        description="0.2.1 reference wizard demonstrating SEQUENCE, ContextBuilder, and CONDITION nodes.",
        version="0.2.1",
        steps=steps,
        on_commit_hook="onboard_new_ape_commit",
        metadata={
            "category": "examples",
            "tags": ["hierarchical", "0.2.1", "SEQUENCE", "CONDITION", "dynamic"],
        },
    )


# ----------------------------------------------------------------------
# Commit handler
# ----------------------------------------------------------------------

def onboard_commit_handler(session: Any) -> dict[str, Any]:
    data = session.collected_data
    name = data.get("ask_name", "Unknown Ape")
    age = data.get("ask_age", "?")
    extra = data.get("ask_employee_id") or data.get("ask_guardian_contact", "N/A")

    return {
        "status": "onboarded",
        "ape_name": name,
        "age": age,
        "extra_info": extra,
        "message": f"Welcome to the troop, {name}!",
    }


COMMIT_HANDLERS = {
    "onboard_new_ape_commit": onboard_commit_handler,
}
