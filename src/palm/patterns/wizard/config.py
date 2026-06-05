"""
Wizard configuration — step definitions and pattern-level options.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

WizardFieldType = Literal["text", "choice", "confirm"]


@dataclass(frozen=True)
class WizardStepConfig:
    """Single interactive wizard step."""

    slug: str
    title: str
    prompt: str
    field_type: WizardFieldType = "text"
    choices: tuple[str, ...] = ()
    required: bool = True

    def __post_init__(self) -> None:
        if not self.slug:
            raise ValueError("Wizard step slug must be non-empty")
        if self.field_type == "choice" and not self.choices:
            raise ValueError(f"Step {self.slug!r} with field_type=choice requires choices")


@dataclass(frozen=True)
class WizardConfig:
    """Full wizard definition."""

    steps: tuple[WizardStepConfig, ...]
    allow_backtrack: bool = True
    introduction_slug: str | None = None

    def __post_init__(self) -> None:
        if not self.steps:
            raise ValueError("WizardConfig requires at least one step")
        slugs = [s.slug for s in self.steps]
        if len(slugs) != len(set(slugs)):
            raise ValueError("Wizard step slugs must be unique")

    @property
    def step_count(self) -> int:
        return len(self.steps)

    def index_of(self, slug: str) -> int:
        for idx, step in enumerate(self.steps):
            if step.slug == slug:
                return idx
        raise KeyError(f"Unknown wizard step slug: {slug!r}")

    @classmethod
    def from_slugs(
        cls,
        slugs: list[str],
        *,
        allow_backtrack: bool = True,
    ) -> WizardConfig:
        """Build a minimal config with auto-generated titles and prompts."""
        steps = tuple(
            WizardStepConfig(
                slug=slug,
                title=slug.replace("_", " ").title(),
                prompt=f"Enter value for {slug}",
            )
            for slug in slugs
        )
        return cls(steps=steps, allow_backtrack=allow_backtrack)