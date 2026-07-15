"""
Wizard job inspection — the wizard pattern owns extraction of its own step,
prompt, collection, transform, and schema context. Implements the
:class:`~palm.core.orchestration.input_capable.JobInspectable` capability so the
shared inspector never branches on the wizard type.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, cast

from palm.common.job_inspection import (
    JobContext,
    choices,
    collection_from_bundle,
    dict_from_bundle,
    field_type,
    int_from_bundle,
    prompt_text,
    prompt_title,
    str_from_bundle,
    transform_from_bundle,
    validation_from_bundle,
)
from palm.core.orchestration import Job
from palm.patterns.wizard.bindings.context.keys import WizardKeys
from palm.patterns.wizard.flow.collection.selection import default_label_field
from palm.states import BlackboardState

if TYPE_CHECKING:
    from palm.patterns.wizard.pattern import WizardPattern


def inspect_wizard_job(wizard: WizardPattern, job: Job) -> JobContext:
    """Build the operator-facing context for a wizard job."""
    state = _as_blackboard(job.state)
    prompt_bundle = _prompt_from_state(state)
    answers = wizard.answers(state)

    collection_items, collection_phase, collection_item_previews = collection_from_bundle(
        prompt_bundle,
    )
    step_slug = wizard.current_step_slug(state)
    step_config = wizard.config.get_step(step_slug) if step_slug else None
    step_kind = step_config.step_kind if step_config is not None else None
    min_items = step_config.min_items if step_config is not None else 1
    label_field: str | None = None
    item_fields: tuple[dict[str, Any], ...] = ()
    if step_config is not None and step_config.step_kind == "collection":
        label_field = default_label_field(
            step_config.item_fields,
            explicit=step_config.label_field,
        )
        item_fields = tuple(
            {
                "slug": field.slug,
                "title": field.title,
                "prompt": field.prompt,
                "field_type": field.field_type,
                "choices": list(field.choices),
                "required": field.required,
            }
            for field in step_config.item_fields
        )
    transform_rule, transform_source_key, transform_target_key, transform_source_preview = (
        transform_from_bundle(prompt_bundle)
    )
    waiting_for_child = bool(prompt_bundle.get("waiting_for_child")) if prompt_bundle else False
    return JobContext(
        pattern="wizard",
        step=wizard.current_step_slug(state),
        scope_path=_wizard_scope_path(state, prompt_bundle),
        validation_error=validation_from_bundle(prompt_bundle) or _validation_from_state(state),
        effective_schema_type=_effective_schema_type(state),
        prompt=prompt_text(prompt_bundle),
        prompt_title=prompt_title(prompt_bundle, wizard.current_step_slug(state)),
        field_type=field_type(prompt_bundle),
        choices=choices(prompt_bundle),
        answers_preview=dict(answers) if answers else {},
        collection_items=collection_items,
        collection_phase=collection_phase,
        collection_item_previews=collection_item_previews,
        collection_draft=dict_from_bundle(prompt_bundle, "collection_draft"),
        collection_progress=str_from_bundle(prompt_bundle, "collection_progress"),
        collection_field=str_from_bundle(prompt_bundle, "collection_field"),
        collection_select_action=str_from_bundle(prompt_bundle, "collection_select_action"),
        collection_remove_index=int_from_bundle(prompt_bundle, "collection_remove_index"),
        step_kind=step_kind,
        min_items=min_items,
        label_field=label_field,
        item_fields=item_fields,
        transform_rule=transform_rule,
        transform_source_key=transform_source_key,
        transform_target_key=transform_target_key,
        transform_source_preview=transform_source_preview,
        waiting_for_child=waiting_for_child,
        waiting_for_child_job_id=str_from_bundle(prompt_bundle, "waiting_for_child_job_id"),
        waiting_for_child_instance_id=str_from_bundle(
            prompt_bundle,
            "waiting_for_child_instance_id",
        ),
        child_status=str_from_bundle(prompt_bundle, "child_status"),
        commit_hook=str_from_bundle(prompt_bundle, "commit_hook"),
        summary=dict_from_bundle(prompt_bundle, "summary"),
    )


def _as_blackboard(state: Any) -> BlackboardState:
    return cast(BlackboardState, state)


def _prompt_from_state(state: BlackboardState) -> dict[str, Any] | None:
    raw = state.get(WizardKeys.ACTIVE_PROMPT)
    return dict(raw) if isinstance(raw, dict) else None


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


def _validation_from_state(state: BlackboardState) -> str | None:
    error = state.get(WizardKeys.VALIDATION_ERROR)
    return str(error) if error is not None else None


def _effective_schema_type(state: BlackboardState) -> str | None:
    effective = state.effective_schema()
    if effective is None or effective.definition is None:
        return None
    schema_type = effective.definition.get("type")
    return str(schema_type) if schema_type is not None else None
