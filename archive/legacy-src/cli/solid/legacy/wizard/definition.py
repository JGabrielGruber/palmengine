"""
WizardDefinition and supporting classes.

A WizardDefinition is a declarative, immutable (at runtime) description of
a complete interactive workflow. It is registered with the engine once.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from palm.cli.solid.legacy.models.step import StepDefinition


class WizardDefinition(BaseModel):
    """
    Complete declarative definition of an interactive wizard.

    Wizards are registered by ID. The engine uses the definition to drive
    execution, validation, and context generation.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)  # immutable after creation

    id: str = Field(min_length=1, max_length=64)
    name: str = Field(min_length=1, max_length=120)
    description: str = Field(default="", max_length=2000)
    version: str = Field(default="1.0.0")

    # Ordered list of steps. The first step MUST be an INTRODUCTION.
    steps: list[StepDefinition] = Field(min_length=1)

    # Optional overrides
    entry_step: str | None = Field(
        default=None,
        description="Slug of first step. Defaults to steps[0].",
    )
    on_commit_hook: str | None = Field(
        default=None,
        description="Name of a registered commit handler (see registry).",
    )

    # Arbitrary metadata (category, tags, author, etc.)
    metadata: dict[str, Any] = Field(default_factory=dict)

    def __post_init__(self) -> None:
        self._validate_structure()

    def _validate_structure(self) -> None:
        """Basic structural validation at definition time."""
        if not self.steps:
            raise ValueError("Wizard must have at least one step")

        first = self.steps[0]
        if first.type != "introduction":
            raise ValueError(
                f"First step of wizard '{self.id}' must be of type 'introduction', "
                f"got '{first.type}'"
            )

        slugs = [s.slug for s in self.steps]
        if len(slugs) != len(set(slugs)):
            dupes = {s for s in slugs if slugs.count(s) > 1}
            raise ValueError(f"Duplicate step slugs in wizard '{self.id}': {dupes}")

        # Ensure introduction is not backtrackable (enforced later too)
        if first.is_backtrackable:
            # We allow definition to say True, but engine will treat it as False
            pass

    def get_step(self, slug: str) -> StepDefinition | None:
        for step in self.steps:
            if step.slug == slug:
                return step
            # Recursive search for children (future-proof)
            if step.children:
                for child in step.children:
                    if child.slug == slug:
                        return child
        return None

    def get_step_index(self, slug: str) -> int | None:
        for i, step in enumerate(self.steps):
            if step.slug == slug:
                return i
        return None

    def get_next_step_slug(self, current_slug: str, data: dict[str, Any]) -> str | None:
        """
        Resolve the next step.

        Priority:
        1. Step's explicit next_step
        2. Next step in definition order
        3. None (terminal)
        """
        step = self.get_step(current_slug)
        if not step:
            return None

        if step.next_step:
            return step.next_step

        idx = self.get_step_index(current_slug)
        if idx is not None and idx + 1 < len(self.steps):
            return self.steps[idx + 1].slug
        return None

    @property
    def introduction_step(self) -> StepDefinition:
        return self.steps[0]

    def iter_steps(self) -> list[StepDefinition]:
        """Return all steps (flat for v0.1)."""
        return list(self.steps)
