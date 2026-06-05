"""
StepDefinition - the atomic unit of a wizard.

Steps are declarative. The WizardEngine interprets them at runtime.

DEPRECATION NOTICE
------------------
Legacy model (moved 0.3.0-dev from palm/models/). Part of the deprecated reference implementation only.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from .common import StepType, ValidationRule


class StepDefinition(BaseModel):
    """
    Declarative definition of a single step in a wizard.

    Hierarchical support is prepared via optional `children` (future Behavior Tree style).
    For v0.1 most wizards will use a flat list with explicit `next_step` or dynamic resolution.
    """

    model_config = ConfigDict(extra="forbid", validate_default=True)

    # Identity & navigation
    slug: str = Field(
        min_length=1, max_length=64, description="Unique identifier within the wizard"
    )
    type: StepType

    # Human presentation
    title: str = Field(min_length=1, max_length=120)
    prompt: str | None = Field(
        default=None,
        description="Primary question or instruction shown to the user",
    )
    guidelines: str | None = Field(
        default=None,
        description="Help text, constraints, or examples shown alongside the prompt",
    )
    description: str | None = Field(default=None, description="Longer explanation (admin/debug)")

    # Input / choice configuration
    choices: list[dict[str, Any]] | None = Field(
        default=None,
        description="For CHOICE steps: [{'value': 'yes', 'label': 'Yes, continue'}]",
    )
    input_schema: dict[str, Any] | None = Field(
        default=None,
        description="Optional JSON Schema or simple type hint for the expected input",
    )

    # Validation
    validation_rules: list[ValidationRule] = Field(default_factory=list)
    required: bool = Field(default=True)

    # Flow control
    next_step: str | None = Field(
        default=None,
        description="Static slug of the next step. If None, engine uses definition order or dynamic logic.",
    )
    is_backtrackable: bool = Field(
        default=True,
        description="Whether users may return to this step via the back command",
    )

    # Extensibility
    metadata: dict[str, Any] = Field(default_factory=dict)
    children: list[StepDefinition] | None = Field(
        default=None,
        description="Optional nested sub-steps (hierarchical / sub-wizard)",
    )

    def is_terminal(self) -> bool:
        return self.type in (StepType.COMMIT,)

    def requires_user_input(self) -> bool:
        return self.type in (
            StepType.USER_INPUT,
            StepType.CHOICE,
            StepType.CONFIRM,
            StepType.INTRODUCTION,
            StepType.SUMMARY,
        )
