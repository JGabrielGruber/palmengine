"""
Wizard configuration — step definitions and pattern-level options.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Literal

from palm.patterns.wizard.bindings.definitions.kinds import PROTECTED_KINDS, WizardStepKind
from palm.patterns.wizard.flow.collection.config import CollectionFieldConfig
from palm.patterns.wizard.flow.validation import StepValidationRule

if TYPE_CHECKING:
    from palm.common.persistence.definition_repository import DefinitionRepository
    from palm.common.transforms.builder import TransformStepSpec
    from palm.core.context import StateSchema

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
    state_schema: dict[str, Any] | None = None
    state_schema_ref: str | None = None
    schema: StateSchema | None = None
    commit_hook: str | None = None
    resource_ref: str | None = None
    resource_action: str | None = None
    params: dict[str, Any] = field(default_factory=dict)
    output_key: str | None = None
    allow_backtrack: bool | None = None
    collection_key: str | None = None
    item_fields: tuple[CollectionFieldConfig, ...] = ()
    min_items: int = 1
    label_field: str | None = None
    transform: TransformStepSpec | None = None
    when: dict[str, Any] | None = None
    then_steps: tuple[WizardStepConfig, ...] = ()
    else_steps: tuple[WizardStepConfig, ...] = ()

    def __post_init__(self) -> None:
        if not self.slug:
            raise ValueError("Wizard step slug must be non-empty")
        if self.field_type == "choice" and not self.choices:
            raise ValueError(f"Step {self.slug!r} with field_type=choice requires choices")
        if self.step_kind == "commit" and not self.commit_hook:
            object.__setattr__(self, "field_type", "confirm")
        if self.step_kind == "collection":
            if not self.item_fields:
                raise ValueError(f"Collection step {self.slug!r} requires item_fields")
            if not self.collection_key:
                object.__setattr__(self, "collection_key", self.slug)
        if self.step_kind == "transform" and self.transform is None:
            raise ValueError(f"Transform step {self.slug!r} requires transform configuration")
        if self.step_kind == "resource" and not self.resource_ref:
            raise ValueError(f"Resource step {self.slug!r} requires resource_ref")
        if self.step_kind == "branch":
            from palm.patterns.wizard.flow.branch.predicate import validate_when_clause

            if not self.when:
                raise ValueError(f"Branch step {self.slug!r} requires when")
            validate_when_clause(self.when)
            if not self.then_steps and not self.else_steps:
                raise ValueError(
                    f"Branch step {self.slug!r} requires at least one nested step in then or else",
                )

    @property
    def has_state_schema(self) -> bool:
        """Return whether inline or referenced step schema is configured."""
        return (
            self.state_schema is not None
            or self.state_schema_ref is not None
            or self.schema is not None
        )

    def materialize_state_schema(
        self,
        repository: DefinitionRepository | None = None,
    ) -> StateSchema | None:
        """Resolve inline schema first, then a repository reference."""
        if self.schema is not None:
            return self.schema
        from palm.common.state.schema_binding import materialize_state_schema

        return materialize_state_schema(
            inline=self.state_schema,
            ref=self.state_schema_ref,
            repository=repository,
        )

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
        slugs = [s.slug for s in self.iter_all_steps()]
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

    def iter_all_steps(self) -> tuple[WizardStepConfig, ...]:
        """Flatten spine steps and nested branch arms for slug validation."""
        flattened: list[WizardStepConfig] = []
        for step in self.iter_tree_steps():
            flattened.extend(_flatten_step_tree(step))
        return tuple(flattened)

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


def _flatten_step_tree(step: WizardStepConfig) -> list[WizardStepConfig]:
    items = [step]
    if step.step_kind == "branch":
        for nested in (*step.then_steps, *step.else_steps):
            items.extend(_flatten_step_tree(nested))
    return items
