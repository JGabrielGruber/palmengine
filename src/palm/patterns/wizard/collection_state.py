"""
Collection step state — list storage, phases, and per-item scopes.
"""

from __future__ import annotations

from typing import Any, Literal, cast

from palm.core.context import BaseState
from palm.patterns.wizard.collection import CollectionFieldConfig
from palm.patterns.wizard.config import WizardStepConfig
from palm.patterns.wizard.keys import WizardKeys
from palm.patterns.wizard.state import enter_step, get_answers, leave_step, set_answers

CollectionPhase = Literal["menu", "field", "remove_confirm", "select_item"]

ACTION_ADD = "__collection_add__"
ACTION_DONE = "__collection_done__"
ACTION_EDIT_SELECT = "__collection_edit_select__"
ACTION_REMOVE_SELECT = "__collection_remove_select__"


def collection_phase(state: BaseState) -> CollectionPhase:
    raw = state.get(WizardKeys.COLLECTION_PHASE)
    if raw in ("menu", "field", "remove_confirm", "select_item"):
        return cast(CollectionPhase, raw)
    return "menu"


def set_collection_phase(state: BaseState, phase: CollectionPhase) -> None:
    state.set(WizardKeys.COLLECTION_PHASE, phase)


def collection_edit_index(state: BaseState) -> int | None:
    raw = state.get(WizardKeys.COLLECTION_EDIT_INDEX)
    return int(raw) if isinstance(raw, int) else None


def set_collection_edit_index(state: BaseState, index: int | None) -> None:
    if index is None:
        state.delete(WizardKeys.COLLECTION_EDIT_INDEX)
    else:
        state.set(WizardKeys.COLLECTION_EDIT_INDEX, index)


def collection_field_index(state: BaseState) -> int:
    raw = state.get(WizardKeys.COLLECTION_FIELD_INDEX)
    return int(raw) if isinstance(raw, int) else 0


def set_collection_field_index(state: BaseState, index: int) -> None:
    state.set(WizardKeys.COLLECTION_FIELD_INDEX, index)


def collection_draft(state: BaseState) -> dict[str, Any]:
    raw = state.get(WizardKeys.COLLECTION_DRAFT)
    return dict(raw) if isinstance(raw, dict) else {}


def set_collection_draft(state: BaseState, draft: dict[str, Any]) -> None:
    if draft:
        state.set(WizardKeys.COLLECTION_DRAFT, dict(draft))
    else:
        state.delete(WizardKeys.COLLECTION_DRAFT)


def clear_collection_session(state: BaseState) -> None:
    state.delete(WizardKeys.COLLECTION_PHASE)
    state.delete(WizardKeys.COLLECTION_EDIT_INDEX)
    state.delete(WizardKeys.COLLECTION_FIELD_INDEX)
    state.delete(WizardKeys.COLLECTION_DRAFT)
    state.delete(WizardKeys.COLLECTION_REMOVE_INDEX)
    state.delete(WizardKeys.COLLECTION_SELECT_ACTION)


def collection_select_action(state: BaseState) -> str | None:
    raw = state.get(WizardKeys.COLLECTION_SELECT_ACTION)
    if raw in ("edit", "remove"):
        return str(raw)
    return None


def set_collection_select_action(state: BaseState, action: str | None) -> None:
    if action is None:
        state.delete(WizardKeys.COLLECTION_SELECT_ACTION)
    else:
        state.set(WizardKeys.COLLECTION_SELECT_ACTION, action)


def collection_remove_index(state: BaseState) -> int | None:
    raw = state.get(WizardKeys.COLLECTION_REMOVE_INDEX)
    return int(raw) if isinstance(raw, int) else None


def set_collection_remove_index(state: BaseState, index: int | None) -> None:
    if index is None:
        state.delete(WizardKeys.COLLECTION_REMOVE_INDEX)
    else:
        state.set(WizardKeys.COLLECTION_REMOVE_INDEX, index)


def get_collection_items(state: BaseState, key: str) -> list[dict[str, Any]]:
    answers = get_answers(state)
    raw = answers.get(key)
    if isinstance(raw, list):
        return [dict(item) for item in raw if isinstance(item, dict)]
    return []


def set_collection_items(
    state: BaseState,
    key: str,
    items: list[dict[str, Any]],
) -> None:
    answers = get_answers(state)
    answers[key] = [dict(item) for item in items]
    set_answers(state, answers)
    if state.schema is not None:
        state.set_validated(key, answers[key])


def item_scope_name(index: int) -> str:
    return f"item-{index}"


def field_scope_name(index: int, field_slug: str) -> str:
    return f"{item_scope_name(index)}:{field_slug}"


def enter_field_scope(
    state: BaseState,
    step: WizardStepConfig,
    field: CollectionFieldConfig,
    index: int,
    *,
    context: Any | None = None,
) -> str:
    """Enter collection, item, and field scopes without duplicating stack frames."""
    ensure_scope(state, step.slug, step=step, context=context)
    ensure_scope(state, item_scope_name(index), context=context)
    scope = field_scope_name(index, field.slug)
    enter_step(state, scope, step=field_as_step(field), context=context)
    return scope


def leave_field_scope(
    state: BaseState,
    field: CollectionFieldConfig,
    index: int,
    *,
    context: Any | None = None,
) -> None:
    leave_step(state, field_scope_name(index, field.slug), context=context)


def leave_item_scope(
    state: BaseState,
    step: WizardStepConfig,
    index: int,
    *,
    context: Any | None = None,
) -> None:
    stack = state.scope_stack()
    item = item_scope_name(index)
    while state.current_scope() is not None and state.current_scope() != step.slug:
        leave_step(state, state.current_scope() or "", context=context)
    if item in stack and state.current_scope() == item:
        leave_step(state, item, context=context)


def ensure_scope(
    state: BaseState,
    name: str,
    *,
    step: WizardStepConfig | None = None,
    context: Any | None = None,
) -> None:
    stack = state.scope_stack()
    if name in stack:
        return
    enter_step(state, name, step=step, context=context)


def field_as_step(field: CollectionFieldConfig) -> WizardStepConfig:
    """Adapt a collection field to a wizard step for shared validation helpers."""
    return WizardStepConfig(
        slug=field.slug,
        title=field.title,
        prompt=field.prompt,
        field_type=field.field_type,
        choices=field.choices,
        required=field.required,
        validation=field.validation,
        state_schema=field.state_schema,
        state_schema_ref=field.state_schema_ref,
        schema=field.schema,
    )


def normalize_optional_field_value(field: CollectionFieldConfig, value: Any) -> Any:
    if field.required:
        return value
    if value is None:
        return None
    if isinstance(value, str) and value.strip() == "":
        return None
    return value


def format_item_label(
    item: dict[str, Any],
    *,
    index: int,
    label_field: str = "title",
    item_fields: tuple[CollectionFieldConfig, ...] | None = None,
) -> str:
    from palm.patterns.wizard.collection_selection import format_item_preview

    return format_item_preview(
        item,
        index=index,
        label_field=label_field,
        item_fields=item_fields,
    )
