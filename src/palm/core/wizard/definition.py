"""
WizardDefinition and supporting classes.

A WizardDefinition is a declarative, immutable (at runtime) description of
a complete interactive workflow. It is registered with the engine once.
"""

from __future__ import annotations

from typing import Any, Callable

from pydantic import BaseModel, ConfigDict, Field

from palm.models.common import StepType
from palm.models.step import StepDefinition
from palm.utils.logging import logger


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

    # ------------------------------------------------------------------
    # Tree-aware helpers (0.2.0 Hierarchical Support)
    # ------------------------------------------------------------------

    def get_step(self, slug: str) -> StepDefinition | None:
        """Find a step by slug anywhere in the tree (depth-first)."""
        for step in self.steps:
            if step.slug == slug:
                return step
            if step.children:
                for child in step.children:
                    if child.slug == slug:
                        return child
                    # Support deeper nesting if needed in future
                    found = self._find_in_children(child, slug)
                    if found:
                        return found
        return None

    def _find_in_children(self, step: StepDefinition, slug: str) -> StepDefinition | None:
        if not step.children:
            return None
        for child in step.children:
            if child.slug == slug:
                return child
            found = self._find_in_children(child, slug)
            if found:
                return found
        return None

    def get_step_by_path(self, path: list[str]) -> StepDefinition | None:
        """Resolve a step using a full path (e.g. ['personal_info', 'ask_name'])."""
        if not path:
            return None
        current: StepDefinition | None = None

        # Start from top level
        for top in self.steps:
            if top.slug == path[0]:
                current = top
                break

        if current is None:
            return None

        for slug in path[1:]:
            if not current.children:
                return None
            current = current.get_child_by_slug(slug)
            if current is None:
                return None
        return current

    def get_children(self, step: StepDefinition) -> list[StepDefinition]:
        return step.children or []

    def is_composite(self, step: StepDefinition) -> bool:
        return bool(step.children)

    def get_next_path(self, current_path: list[str], data: dict[str, Any]) -> list[str] | None:
        """
        Core 0.2.1 stabilized tree navigation.

        Given the current full path, returns the next path to visit (or None for terminal).
        Handles explicit next_step, descending into SEQUENCE/CONDITION composites,
        CONDITION predicate evaluation, and sibling/parent ascent.
        """
        if not current_path:
            logger.debug("get_next_path: empty current_path")
            return None

        current_step = self.get_step_by_path(current_path)
        if not current_step:
            logger.warning(f"get_next_path: could not resolve step for path {current_path}")
            return None

        logger.debug(f"get_next_path: at {current_path} (type={current_step.type}, has_children={bool(current_step.children)})")

        # 1. Explicit next_step wins (can jump anywhere)
        if current_step.next_step:
            target = self.get_step(current_step.next_step)
            if target:
                resolved = self._resolve_path_to_step(target.slug) or [current_step.next_step]
                logger.debug(f"  -> explicit next_step '{current_step.next_step}' resolved to {resolved}")
                return resolved

        # 2. Composite handling: descend
        if current_step.children:
            if current_step.type == StepType.CONDITION:
                # 0.2.2: Explicit and strict CONDITION branching
                # children[0] = True branch, children[1] = False branch
                cond = current_step.condition
                take_true_branch = True

                if cond is not None and callable(cond):
                    try:
                        take_true_branch = bool(cond(data))
                    except Exception as exc:
                        logger.warning(f"CONDITION predicate failed for {current_path}: {exc}. Defaulting to True branch.")
                        take_true_branch = True

                branch_idx = 0 if take_true_branch else 1

                if current_step.children and branch_idx < len(current_step.children):
                    child = current_step.children[branch_idx]
                    next_path = current_path + [child.slug]
                    logger.info(f"CONDITION at {current_path} evaluated to {take_true_branch} → choosing child '{child.slug}'")
                    return next_path

                # Safe fallback
                if current_step.children:
                    next_path = current_path + [current_step.children[0].slug]
                    logger.warning(f"CONDITION fallback at {current_path} → first child")
                    return next_path

                logger.warning(f"CONDITION at {current_path} has no children")
                return self._find_next_sibling_or_ascend(current_path)

            # Default for any composite with children (SEQUENCE or untyped container): descend to first child
            next_path = current_path + [current_step.children[0].slug]
            logger.debug(f"  -> descending composite {current_step.type} to first child {next_path}")
            return next_path

        # 3. Leaf: find next sibling or ascend
        next_path = self._find_next_sibling_or_ascend(current_path)
        logger.debug(f"  -> leaf, next sibling/ascend resolved to {next_path}")
        return next_path

    def _resolve_path_to_step(self, target_slug: str) -> list[str] | None:
        """Attempt to build a path that reaches the given slug."""
        def search(steps: list[StepDefinition], prefix: list[str]) -> list[str] | None:
            for s in steps:
                current_path = prefix + [s.slug]
                if s.slug == target_slug:
                    return current_path
                if s.children:
                    found = search(s.children, current_path)
                    if found:
                        return found
            return None

        return search(self.steps, [])

    def _find_next_sibling_or_ascend(self, path: list[str]) -> list[str] | None:
        """Find the next sibling after the last element in path, or ascend and continue."""
        logger.debug(f"    _find_next_sibling_or_ascend from {path}")

        if len(path) <= 1:
            # Top-level leaf
            top_slug = path[0]
            top_step = self.get_step(top_slug)
            if top_step and top_step.next_step:
                return [top_step.next_step]
            idx = self._get_top_level_index(top_slug)
            if idx is not None and idx + 1 < len(self.steps):
                return [self.steps[idx + 1].slug]
            logger.debug("    -> no more top-level siblings, terminal")
            return None

        parent_path = path[:-1]
        parent = self.get_step_by_path(parent_path)
        if not parent or not parent.children:
            return self._find_next_sibling_or_ascend(parent_path)

        current_slug = path[-1]
        try:
            child_idx = [c.slug for c in parent.children].index(current_slug)
        except ValueError:
            return self._find_next_sibling_or_ascend(parent_path)

        if child_idx + 1 < len(parent.children):
            nextp = parent_path + [parent.children[child_idx + 1].slug]
            logger.debug(f"    -> next sibling {nextp}")
            return nextp

        # Ascend
        logger.debug(f"    -> no more siblings under {parent_path}, ascending")
        return self._find_next_sibling_or_ascend(parent_path)

    def _get_top_level_index(self, slug: str) -> int | None:
        for i, s in enumerate(self.steps):
            if s.slug == slug:
                return i
        return None

    @property
    def introduction_step(self) -> StepDefinition:
        return self.steps[0]

    def iter_steps(self, include_children: bool = False) -> list[StepDefinition]:
        """Return steps. If include_children=True, performs a full tree traversal."""
        if not include_children:
            return list(self.steps)

        result: list[StepDefinition] = []
        for step in self.steps:
            result.append(step)
            if step.children:
                result.extend(self._flatten_children(step))
        return result

    def _flatten_children(self, step: StepDefinition) -> list[StepDefinition]:
        out: list[StepDefinition] = []
        if step.children:
            for c in step.children:
                out.append(c)
                out.extend(self._flatten_children(c))
        return out

    def get_breadcrumb(self, path: list[str]) -> str:
        """Human friendly path for display."""
        return " / ".join(path) if path else ""
