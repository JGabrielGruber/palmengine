"""
Parallel job inspection — the parallel pattern owns extraction of its own branch
statuses, active scope, merge preview, and per-branch prompt context. Implements
the :class:`~palm.core.orchestration.input_capable.JobInspectable` capability so
the shared inspector never branches on the parallel type.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, cast

from palm.common.job_inspection import (
    BranchStatus,
    JobContext,
    choices,
    dict_from_bundle,
    field_type,
    prompt_text,
    prompt_title,
    str_from_bundle,
    validation_from_bundle,
)
from palm.common.persistence.state_snapshot import state_from_snapshot
from palm.core.orchestration import Job
from palm.patterns.parallel.bindings.context.keys import ParallelKeys
from palm.patterns.parallel.flow.merge import get_branch_results
from palm.patterns.parallel.flow.scope import load_branch_snapshot_for
from palm.patterns.wizard.bindings.context.keys import WizardKeys
from palm.states import BlackboardState

if TYPE_CHECKING:
    from palm.patterns.parallel.pattern import ParallelPattern


def inspect_parallel_job(parallel: ParallelPattern, job: Job) -> JobContext:
    """Build the operator-facing context for a parallel job."""
    state = _as_blackboard(job.state)
    active = state.get(ParallelKeys.ACTIVE_BRANCH)
    active_slug = str(active) if isinstance(active, str) else None
    branches = _parallel_branch_status(parallel, state, active_slug)
    step = parallel.current_step_slug(state)
    scope_path = _parallel_scope_path(active_slug, step)

    branch_state = _load_active_branch_state(state, active_slug)
    prompt_bundle = _prompt_from_state(branch_state) if branch_state else None

    validation = validation_from_bundle(prompt_bundle)
    if validation is None and branch_state is not None:
        error = branch_state.get(WizardKeys.VALIDATION_ERROR)
        validation = str(error) if error is not None else None

    merged = state.get(ParallelKeys.MERGED)
    merged_preview = dict(merged) if isinstance(merged, dict) else {}
    results = get_branch_results(state)

    top_prompt = _prompt_from_state(state)
    return JobContext(
        pattern="parallel",
        step=step,
        scope_path=scope_path,
        active_branch=active_slug,
        branches=branches,
        validation_error=validation,
        effective_schema_type=_effective_schema_type(state),
        prompt=prompt_text(prompt_bundle),
        prompt_title=prompt_title(prompt_bundle, active_slug),
        field_type=field_type(prompt_bundle),
        choices=choices(prompt_bundle),
        answers_preview=dict(results) if results else {},
        merged_preview=merged_preview,
        commit_hook=str_from_bundle(top_prompt, "commit_hook"),
        summary=dict_from_bundle(top_prompt, "summary"),
    )


def _as_blackboard(state: Any) -> BlackboardState:
    return cast(BlackboardState, state)


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


def _effective_schema_type(state: BlackboardState) -> str | None:
    effective = state.effective_schema()
    if effective is None or effective.definition is None:
        return None
    schema_type = effective.definition.get("type")
    return str(schema_type) if schema_type is not None else None
