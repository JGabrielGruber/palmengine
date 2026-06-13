"""
Job context extraction — scopes, branches, schemas, and validation (mode-agnostic).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, cast

from palm.common.persistence.state_snapshot import state_from_snapshot
from palm.core.orchestration import Job
from palm.patterns.parallel.keys import ParallelKeys
from palm.patterns.parallel.merge import get_branch_results
from palm.patterns.parallel.pattern import ParallelPattern
from palm.patterns.parallel.scope import load_branch_snapshot_for
from palm.patterns.wizard.keys import WizardKeys
from palm.patterns.wizard.pattern import WizardPattern
from palm.states import BlackboardState


def _as_blackboard(state: Any) -> BlackboardState:
    """Narrow job state to ``BlackboardState`` for CLI inspection helpers."""
    return cast(BlackboardState, state)


@dataclass(frozen=True)
class BranchStatus:
    slug: str
    completed: bool
    active: bool
    step: str | None = None


@dataclass(frozen=True)
class JobContext:
    """Operator-facing snapshot of a waiting or running job."""

    pattern: str
    step: str | None = None
    scope_path: str | None = None
    active_branch: str | None = None
    branches: tuple[BranchStatus, ...] = ()
    validation_error: str | None = None
    effective_schema_type: str | None = None
    prompt: str | None = None
    prompt_title: str | None = None
    field_type: str | None = None
    choices: tuple[str, ...] = ()
    answers_preview: dict[str, Any] = field(default_factory=dict)
    merged_preview: dict[str, Any] = field(default_factory=dict)
    collection_items: tuple[dict[str, Any], ...] = ()
    collection_phase: str | None = None
    collection_item_previews: tuple[str, ...] = ()

    @property
    def repl_scope_suffix(self) -> str:
        """Compact suffix for the REPL prompt."""
        if self.scope_path:
            return f"@{self.scope_path}"
        if self.active_branch:
            return f"@parallel:{self.active_branch}"
        return ""

    @property
    def branch_progress(self) -> str | None:
        if not self.branches:
            return None
        done = sum(1 for branch in self.branches if branch.completed)
        return f"{done}/{len(self.branches)}"


def format_step_context(step_slug: str | None) -> str:
    """Compact context label for instance tables from a persisted step slug."""
    if not step_slug:
        return "—"
    if ":" in step_slug:
        branch, inner = step_slug.split(":", 1)
        if inner:
            return f"parallel:{branch} > {inner}"
        return f"parallel:{branch}"
    return step_slug


def instance_id_for_job(job: Job) -> str:
    raw = job.metadata.get("instance_id")
    return str(raw) if raw else job.id


def inspect_job(job: Job) -> JobContext:
    """Build a display context from a live orchestration job."""
    executable = job.executable

    if isinstance(executable, ParallelPattern):
        return _inspect_parallel(job, executable)
    if isinstance(executable, WizardPattern):
        return _inspect_wizard(job, executable)
    return JobContext(pattern=getattr(executable, "name", "unknown"))


def inspect_job_json(job: Job) -> dict[str, Any]:
    """JSON-serializable job context for ``status --format json``."""
    ctx = inspect_job(job)
    payload: dict[str, Any] = {
        "pattern": ctx.pattern,
        "step": ctx.step,
        "scope_path": ctx.scope_path,
        "active_branch": ctx.active_branch,
        "validation_error": ctx.validation_error,
        "effective_schema_type": ctx.effective_schema_type,
        "prompt": ctx.prompt,
        "field_type": ctx.field_type,
        "answers": ctx.answers_preview,
    }
    if ctx.branches:
        payload["branches"] = [
            {
                "slug": branch.slug,
                "completed": branch.completed,
                "active": branch.active,
                "step": branch.step,
            }
            for branch in ctx.branches
        ]
        payload["branch_progress"] = ctx.branch_progress
    if ctx.merged_preview:
        payload["merged"] = ctx.merged_preview
    return payload


def _inspect_parallel(job: Job, parallel: ParallelPattern) -> JobContext:
    state = _as_blackboard(job.state)
    active = state.get(ParallelKeys.ACTIVE_BRANCH)
    active_slug = str(active) if isinstance(active, str) else None
    branches = _parallel_branch_status(parallel, state, active_slug)
    step = parallel.current_step_slug(state)
    scope_path = _parallel_scope_path(active_slug, step)

    branch_state = _load_active_branch_state(state, active_slug)
    prompt_bundle = _prompt_from_state(branch_state) if branch_state else None

    validation = _validation_from_bundle(prompt_bundle)
    if validation is None and branch_state is not None:
        error = branch_state.get(WizardKeys.VALIDATION_ERROR)
        validation = str(error) if error is not None else None

    merged = state.get(ParallelKeys.MERGED)
    merged_preview = dict(merged) if isinstance(merged, dict) else {}
    results = get_branch_results(state)

    return JobContext(
        pattern="parallel",
        step=step,
        scope_path=scope_path,
        active_branch=active_slug,
        branches=branches,
        validation_error=validation,
        effective_schema_type=_effective_schema_type(state),
        prompt=_prompt_text(prompt_bundle),
        prompt_title=_prompt_title(prompt_bundle, active_slug),
        field_type=_field_type(prompt_bundle),
        choices=_choices(prompt_bundle),
        answers_preview=dict(results) if results else {},
        merged_preview=merged_preview,
    )


def _inspect_wizard(job: Job, wizard: WizardPattern) -> JobContext:
    state = _as_blackboard(job.state)
    prompt_bundle = _prompt_from_state(state)
    answers = wizard.answers(state)

    collection_items, collection_phase, collection_item_previews = _collection_from_bundle(
        prompt_bundle,
    )
    return JobContext(
        pattern="wizard",
        step=wizard.current_step_slug(state),
        scope_path=_wizard_scope_path(state, prompt_bundle),
        validation_error=_validation_from_bundle(prompt_bundle) or _validation_from_state(state),
        effective_schema_type=_effective_schema_type(state),
        prompt=_prompt_text(prompt_bundle),
        prompt_title=_prompt_title(prompt_bundle, wizard.current_step_slug(state)),
        field_type=_field_type(prompt_bundle),
        choices=_choices(prompt_bundle),
        answers_preview=dict(answers) if answers else {},
        collection_items=collection_items,
        collection_phase=collection_phase,
        collection_item_previews=collection_item_previews,
    )


def _parallel_branch_status(
    parallel: ParallelPattern,
    state: BlackboardState,
    active_slug: str | None,
) -> tuple[BranchStatus, ...]:
    items: list[BranchStatus] = []
    for slug, runner in parallel.branch_runners().items():
        step: str | None = None
        if not runner.completed:
            raw_step = runner.current_step_slug(state)
            if isinstance(raw_step, str) and raw_step.startswith(f"{slug}:"):
                step = raw_step.split(":", 1)[1]
            else:
                step = raw_step
        items.append(
            BranchStatus(
                slug=slug,
                completed=runner.completed,
                active=slug == active_slug,
                step=step,
            ),
        )
    return tuple(items)


def _parallel_scope_path(active_slug: str | None, step: str | None) -> str | None:
    parts: list[str] = []
    if active_slug:
        parts.append(f"parallel:{active_slug}")
    elif step and ":" in step:
        branch, inner = step.split(":", 1)
        parts.append(f"parallel:{branch}")
        if inner:
            parts.append(inner)
    elif step:
        parts.append(f"parallel:{step}")
    return " > ".join(parts) if parts else None


def _wizard_scope_path(state: BlackboardState, prompt: dict[str, Any] | None) -> str | None:
    if prompt:
        current = prompt.get("current_scope")
        if isinstance(current, str) and current:
            return current
        stack = prompt.get("scope_stack")
        if isinstance(stack, list) and stack:
            return " > ".join(str(item) for item in stack)
    scope = state.current_scope()
    return str(scope) if scope is not None else None


def _load_active_branch_state(
    parent: BlackboardState,
    active_slug: str | None,
) -> BlackboardState | None:
    if not active_slug:
        return None
    snapshot = load_branch_snapshot_for(parent, active_slug)
    if not snapshot:
        return None
    return state_from_snapshot(snapshot)


def _prompt_from_state(state: BlackboardState) -> dict[str, Any] | None:
    raw = state.get(WizardKeys.ACTIVE_PROMPT)
    return dict(raw) if isinstance(raw, dict) else None


def _prompt_text(bundle: dict[str, Any] | None) -> str | None:
    if not bundle:
        return None
    prompt = bundle.get("prompt")
    return str(prompt) if prompt is not None else None


def _prompt_title(bundle: dict[str, Any] | None, fallback: str | None) -> str | None:
    if not bundle:
        return fallback
    title = bundle.get("title")
    if title is not None:
        return str(title)
    slug = bundle.get("slug")
    return str(slug) if slug is not None else fallback


def _field_type(bundle: dict[str, Any] | None) -> str | None:
    if not bundle:
        return None
    value = bundle.get("field_type", "text")
    return str(value)


def _collection_from_bundle(
    bundle: dict[str, Any] | None,
) -> tuple[tuple[dict[str, Any], ...], str | None, tuple[str, ...]]:
    if not bundle:
        return (), None, ()
    phase = bundle.get("collection_phase")
    phase_str = str(phase) if phase is not None else None
    previews_raw = bundle.get("collection_item_previews")
    previews = tuple(str(item) for item in previews_raw) if isinstance(previews_raw, list) else ()
    raw = bundle.get("collection_items")
    if isinstance(raw, list):
        items = tuple(dict(item) for item in raw if isinstance(item, dict))
        return items, phase_str, previews
    return (), phase_str, previews


def _choices(bundle: dict[str, Any] | None) -> tuple[str, ...]:
    if not bundle:
        return ()
    raw = bundle.get("choices")
    if isinstance(raw, list):
        return tuple(str(item) for item in raw)
    return ()


def _validation_from_bundle(bundle: dict[str, Any] | None) -> str | None:
    if not bundle:
        return None
    error = bundle.get("validation_error")
    return str(error) if error is not None else None


def _validation_from_state(state: BlackboardState) -> str | None:
    error = state.get(WizardKeys.VALIDATION_ERROR)
    return str(error) if error is not None else None


def _effective_schema_type(state: BlackboardState) -> str | None:
    effective = state.effective_schema()
    if effective is None or effective.definition is None:
        return None
    schema_type = effective.definition.get("type")
    return str(schema_type) if schema_type is not None else None
