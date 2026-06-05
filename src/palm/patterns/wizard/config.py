"""
Wizard configuration — step definitions and pattern-level options.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from palm.patterns.wizard.step_kinds import PROTECTED_KINDS, WizardStepKind
from palm.patterns.wizard.validation import StepValidationRule

WizardFieldType = Literal["text", "choice", "confirm"]


@dataclass(frozen=True)
class WizardStepConfig:
    """Single wizard step (input, introduction, summary, commit, or action)."""

    slug: str
    title: str
    prompt: str
    field_type: WizardFieldType = "text"
    choices: tuple[str, ...] = ()
    required: bool = True
    step_kind: WizardStepKind = "input"
    validation: tuple[StepValidationRule, ...] = ()
    commit_hook: str | None = None
    resource_provider: str | None = None
    resource_id: str | None = None
    allow_backtrack: bool | None = None

    def __post_init__(self) -> None:
        if not self.slug:
            raise ValueError("Wizard step slug must be non-empty")
        if self.field_type == "choice" and not self.choices:
            raise ValueError(f"Step {self.slug!r} with field_type=choice requires choices")
        if self.step_kind == "commit" and not self.commit_hook:
            object.__setattr__(self, "field_type", "confirm")

    @property
    def is_protected(self) -> bool:
        if self.step_kind in PROTECTED_KINDS:
            return True
        return self.allow_backtrack is False


@dataclass(frozen=True)
class WizardConfig:
    """Full wizard definition with optional transactional summary/commit."""

    steps: tuple[WizardStepConfig, ...]
    allow_backtrack: bool = True
    introduction_slug: str | None = None
    include_summary: bool = False
    include_commit: bool = False
    summary_slug: str = "summary"
    commit_slug: str = "commit"
    commit_hook: str | None = None

    def __post_init__(self) -> None:
        if not self.steps:
            raise ValueError("WizardConfig requires at least one step")
        slugs = [s.slug for s in self.iter_tree_steps()]
        if len(slugs) != len(set(slugs)):
            raise ValueError("Wizard step slugs must be unique")

    @property
    def step_count(self) -> int:
        return len(tuple(self.iter_tree_steps()))

    def iter_tree_steps(self) -> tuple[WizardStepConfig, ...]:
        """All steps including auto-generated summary and commit steps."""
        items: list[WizardStepConfig] = list(self.steps)
        if self.include_summary and not _has_slug(items, self.summary_slug):
            items.append(self._default_summary_step())
        if self.include_commit and not _has_slug(items, self.commit_slug):
            items.append(self._default_commit_step())
        return tuple(items)

    def protected_slugs(self) -> frozenset[str]:
        slugs: set[str] = set()
        if self.introduction_slug:
            slugs.add(self.introduction_slug)
        if self.include_summary:
            slugs.add(self.summary_slug)
        if self.include_commit:
            slugs.add(self.commit_slug)
        for step in self.iter_tree_steps():
            if step.is_protected:
                slugs.add(step.slug)
        return frozenset(slugs)

    def index_of(self, slug: str) -> int:
        for idx, step in enumerate(self.iter_tree_steps()):
            if step.slug == slug:
                return idx
        raise KeyError(f"Unknown wizard step slug: {slug!r}")

    def get_step(self, slug: str) -> WizardStepConfig | None:
        for step in self.iter_tree_steps():
            if step.slug == slug:
                return step
        return None

    def _default_summary_step(self) -> WizardStepConfig:
        return WizardStepConfig(
            slug=self.summary_slug,
            title="Summary",
            prompt="Review your answers and confirm to continue.",
            field_type="confirm",
            step_kind="summary",
            allow_backtrack=False,
        )

    def _default_commit_step(self) -> WizardStepConfig:
        return WizardStepConfig(
            slug=self.commit_slug,
            title="Commit",
            prompt="Apply changes and finalize?",
            field_type="confirm",
            step_kind="commit",
            commit_hook=self.commit_hook,
            allow_backtrack=False,
        )

    @classmethod
    def from_slugs(
        cls,
        slugs: list[str],
        *,
        allow_backtrack: bool = True,
        include_summary: bool = False,
        include_commit: bool = False,
        commit_hook: str | None = None,
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
        return cls(
            steps=steps,
            allow_backtrack=allow_backtrack,
            include_summary=include_summary,
            include_commit=include_commit,
            commit_hook=commit_hook,
        )


def _has_slug(steps: list[WizardStepConfig], slug: str) -> bool:
    return any(step.slug == slug for step in steps)
