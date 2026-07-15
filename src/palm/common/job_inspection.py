"""
Pattern-agnostic job inspection — operator-facing snapshot of a waiting/running job.

The shared inspector knows only the :class:`~palm.core.orchestration.input_capable.JobInspectable`
capability: each pattern owns the extraction of its own scopes, branches, prompts,
and schemas (see ``palm.patterns.<pattern>.bindings.inspection``). Nothing here
branches on a concrete pattern type.

The bundle-parsing helpers below operate on plain ``dict`` prompt bundles and are
reused by the pattern-side extractors — they are pure and layer-neutral.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from palm.core.orchestration import Job
from palm.core.orchestration.input_capable import JobInspectable


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
    collection_draft: dict[str, Any] = field(default_factory=dict)
    collection_progress: str | None = None
    collection_field: str | None = None
    collection_select_action: str | None = None
    collection_remove_index: int | None = None
    step_kind: str | None = None
    min_items: int = 1
    label_field: str | None = None
    item_fields: tuple[dict[str, Any], ...] = ()
    transform_rule: str | None = None
    transform_source_key: str | None = None
    transform_target_key: str | None = None
    transform_source_preview: str | None = None
    waiting_for_child: bool = False
    waiting_for_child_job_id: str | None = None
    waiting_for_child_instance_id: str | None = None
    child_status: str | None = None
    commit_hook: str | None = None
    summary: dict[str, Any] = field(default_factory=dict)

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


def inspect_job(job: Job) -> JobContext:
    """Build a display context from a live orchestration job (pattern-agnostic)."""
    executable = job.executable
    if isinstance(executable, JobInspectable):
        return executable.inspect_job(job)
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
        "prompt_title": ctx.prompt_title,
        "field_type": ctx.field_type,
        "answers": ctx.answers_preview,
    }
    if ctx.choices:
        payload["choices"] = list(ctx.choices)
    if ctx.collection_phase:
        payload["collection_phase"] = ctx.collection_phase
    if ctx.collection_items:
        payload["collection_items"] = list(ctx.collection_items)
    if ctx.collection_item_previews:
        payload["collection_item_previews"] = list(ctx.collection_item_previews)
    if ctx.collection_draft:
        payload["collection_draft"] = dict(ctx.collection_draft)
    if ctx.collection_progress:
        payload["collection_progress"] = ctx.collection_progress
    if ctx.collection_field:
        payload["collection_field"] = ctx.collection_field
    if ctx.collection_select_action:
        payload["collection_select_action"] = ctx.collection_select_action
    if ctx.collection_remove_index is not None:
        payload["collection_remove_index"] = ctx.collection_remove_index
    if ctx.step_kind:
        payload["step_kind"] = ctx.step_kind
    if ctx.min_items != 1:
        payload["min_items"] = ctx.min_items
    if ctx.label_field:
        payload["label_field"] = ctx.label_field
    if ctx.item_fields:
        payload["item_fields"] = list(ctx.item_fields)
    if ctx.waiting_for_child:
        payload["waiting_for_child"] = True
        payload["waiting_for_child_job_id"] = ctx.waiting_for_child_job_id
        payload["waiting_for_child_instance_id"] = ctx.waiting_for_child_instance_id
        payload["child_status"] = ctx.child_status
    if ctx.transform_rule:
        payload["transform_rule"] = ctx.transform_rule
        payload["transform_source_key"] = ctx.transform_source_key
        payload["transform_target_key"] = ctx.transform_target_key
        payload["transform_source_preview"] = ctx.transform_source_preview
    if ctx.commit_hook:
        payload["commit_hook"] = ctx.commit_hook
    if ctx.summary:
        payload["summary"] = ctx.summary
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


# ── Prompt-bundle helpers — pure dict readers, reused by pattern-side extractors ──


def prompt_text(bundle: dict[str, Any] | None) -> str | None:
    if not bundle:
        return None
    prompt = bundle.get("prompt")
    return str(prompt) if prompt is not None else None


def prompt_title(bundle: dict[str, Any] | None, fallback: str | None) -> str | None:
    if not bundle:
        return fallback
    title = bundle.get("title")
    if title is not None:
        return str(title)
    slug = bundle.get("slug")
    return str(slug) if slug is not None else fallback


def field_type(bundle: dict[str, Any] | None) -> str | None:
    if not bundle:
        return None
    value = bundle.get("field_type", "text")
    return str(value)


def choices(bundle: dict[str, Any] | None) -> tuple[str, ...]:
    if not bundle:
        return ()
    raw = bundle.get("choices")
    if isinstance(raw, list):
        return tuple(str(item) for item in raw)
    return ()


def validation_from_bundle(bundle: dict[str, Any] | None) -> str | None:
    if not bundle:
        return None
    error = bundle.get("validation_error")
    return str(error) if error is not None else None


def transform_from_bundle(
    bundle: dict[str, Any] | None,
) -> tuple[str | None, str | None, str | None, str | None]:
    if not bundle:
        return None, None, None, None
    rule = bundle.get("transform_rule")
    chain = bundle.get("transform_chain")
    rule_label: str | None = None
    if isinstance(chain, list) and chain:
        rule_label = " → ".join(str(item) for item in chain)
    elif rule is not None:
        rule_label = str(rule)
    source = bundle.get("transform_source_key")
    target = bundle.get("transform_target_key")
    preview = bundle.get("transform_source_preview")
    return (
        rule_label,
        str(source) if source is not None else None,
        str(target) if target is not None else None,
        str(preview) if preview is not None else None,
    )


def collection_from_bundle(
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


def dict_from_bundle(bundle: dict[str, Any] | None, key: str) -> dict[str, Any]:
    if not bundle:
        return {}
    raw = bundle.get(key)
    return dict(raw) if isinstance(raw, dict) else {}


def str_from_bundle(bundle: dict[str, Any] | None, key: str) -> str | None:
    if not bundle:
        return None
    raw = bundle.get(key)
    return str(raw) if raw is not None else None


def int_from_bundle(bundle: dict[str, Any] | None, key: str) -> int | None:
    if not bundle:
        return None
    raw = bundle.get(key)
    return int(raw) if isinstance(raw, int) else None
