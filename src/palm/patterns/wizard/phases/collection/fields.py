"""Collection fields phase — BT sequence for per-item field collection."""

from __future__ import annotations

from typing import Any

from palm.core.behavior_tree import LeafNode, PatternStatus, SequenceNode
from palm.core.context import BaseState
from palm.patterns.wizard.collection import CollectionFieldConfig
from palm.patterns.wizard.collection_state import (
    clear_collection_session,
    collection_draft,
    collection_edit_index,
    collection_field_index,
    ensure_scope,
    enter_field_scope,
    field_as_step,
    get_collection_items,
    item_scope_name,
    leave_field_scope,
    leave_item_scope,
    normalize_optional_field_value,
    set_collection_draft,
    set_collection_edit_index,
    set_collection_field_index,
    set_collection_items,
    set_collection_phase,
)
from palm.patterns.wizard.config import WizardStepConfig
from palm.patterns.wizard.events import WizardEventType
from palm.patterns.wizard.leaf_support import build_prompt_bundle, emit_wizard_event
from palm.patterns.wizard.phases._base import EventEmitter
from palm.patterns.wizard.phases.collection._base import CollectionPhaseContext, CollectionPhaseLeaf
from palm.patterns.wizard.validation import (
    prepare_step_input,
    publish_validation_feedback,
    validate_step_input,
)


class CollectionFieldLeaf(LeafNode):
    """One field prompt inside the item field sequence."""

    def __init__(
        self,
        field: CollectionFieldConfig,
        *,
        ctx: CollectionPhaseContext,
    ) -> None:
        super().__init__(f"{ctx.step.slug}.{field.slug}")
        self._field = field
        self._ctx = ctx

    def apply_input(self, value: Any, state: BaseState) -> PatternStatus:
        field_index = collection_field_index(state)
        if field_index >= len(self._ctx.item_fields):
            return PatternStatus.SUCCESS

        value = normalize_optional_field_value(self._field, value)
        step_field = field_as_step(self._field)
        value, choice_error = prepare_step_input(state, step_field, value)
        if choice_error is not None:
            return self._fail(state, choice_error.errors)

        validation = validate_step_input(state, step_field, value)
        if not validation.ok:
            return self._fail(state, validation.errors)

        edit_index = collection_edit_index(state)
        item_index = (
            edit_index
            if edit_index is not None
            else len(get_collection_items(state, self._ctx.collection_key))
        )
        leave_field_scope(state, self._field, item_index, context=self._ctx.context_engine)

        draft = collection_draft(state)
        if value is None:
            draft.pop(self._field.slug, None)
        else:
            draft[self._field.slug] = value
        set_collection_draft(state, draft)
        set_collection_field_index(state, field_index + 1)
        emit_wizard_event(
            self._ctx.emit,
            self._ctx.wizard_name,
            WizardEventType.INPUT_RECEIVED,
            slug=self.name,
            value=value,
            step_index=self._ctx.step_index,
        )
        return PatternStatus.SUCCESS

    def _tick_impl(self, state: BaseState) -> PatternStatus:
        field_index = collection_field_index(state)
        if field_index >= len(self._ctx.item_fields):
            return PatternStatus.SUCCESS
        if self._ctx.item_fields[field_index].slug != self._field.slug:
            return PatternStatus.FAILURE

        edit_index = collection_edit_index(state)
        item_index = (
            edit_index
            if edit_index is not None
            else len(get_collection_items(state, self._ctx.collection_key))
        )
        enter_field_scope(state, self._ctx.step, self._field, item_index, context=self._ctx.context_engine)

        draft = collection_draft(state)
        progress = f"Item field {field_index + 1}/{len(self._ctx.item_fields)}"
        if edit_index is not None:
            progress = f"Editing item #{edit_index + 1} — {progress}"

        bundle = build_prompt_bundle(
            state,
            wizard_name=self._ctx.wizard_name,
            step=self._ctx.step,
            step_index=self._ctx.step_index,
            context=self._ctx.context_engine,
            prompt=self._field.prompt,
            field_type=self._field.field_type,
            choices=list(self._field.choices),
            title=self._field.title,
            step_kind="collection",
            collection_phase="field",
            collection_field=self._field.slug,
            collection_draft=draft,
            collection_progress=progress,
        )
        state.set(f"__bt_prompt__:{self._ctx.step.slug}", bundle)
        return PatternStatus.RUNNING

    def _fail(self, state: BaseState, errors: tuple[str, ...]) -> PatternStatus:
        publish_validation_feedback(
            state,
            errors,
            prompt_bundle=build_prompt_bundle(
                state,
                wizard_name=self._ctx.wizard_name,
                step=self._ctx.step,
                step_index=self._ctx.step_index,
                context=self._ctx.context_engine,
                prompt=self._field.prompt,
                field_type=self._field.field_type,
                choices=list(self._field.choices),
                title=self._field.title,
                step_kind="collection",
                collection_phase="field",
                collection_field=self._field.slug,
                collection_draft=collection_draft(state),
            ),
            prompt_key=f"__bt_prompt__:{self._ctx.step.slug}",
        )
        return PatternStatus.FAILURE


def build_field_sequence(ctx: CollectionPhaseContext) -> SequenceNode:
    children = [CollectionFieldLeaf(field, ctx=ctx) for field in ctx.item_fields]
    return SequenceNode(f"{ctx.step.slug}_fields", children=children)


class CollectionFieldsPhase(CollectionPhaseLeaf):
    phase_key = "field"

    def __init__(self, ctx: CollectionPhaseContext) -> None:
        super().__init__(ctx)
        self._sequence = build_field_sequence(ctx)

    def start_item(self, state: BaseState, *, edit_index: int | None) -> PatternStatus:
        items = get_collection_items(state, self._ctx.collection_key)
        if edit_index is None:
            draft: dict[str, Any] = {}
            index = len(items)
        else:
            draft = dict(items[edit_index])
            index = edit_index

        set_collection_edit_index(state, edit_index)
        set_collection_draft(state, draft)
        set_collection_field_index(state, 0)
        set_collection_phase(state, "field")
        self._sequence.reset()
        ensure_scope(state, self._ctx.step.slug, step=self._ctx.step, context=self._ctx.context_engine)
        ensure_scope(state, item_scope_name(index), context=self._ctx.context_engine)
        return self.run(state, None)

    def _request_input(self, state: BaseState) -> PatternStatus:
        field_index = collection_field_index(state)
        if field_index >= len(self._ctx.item_fields):
            return self._commit_item(state)

        leaf = self._sequence.children[field_index]
        leaf.tick(state)
        bundle = state.get(f"__bt_prompt__:{self._ctx.step.slug}")
        if not isinstance(bundle, dict):
            return PatternStatus.FAILURE
        return self._activate(state, dict(bundle))

    def _handle_input(self, value: Any, state: BaseState) -> PatternStatus:
        field_index = collection_field_index(state)
        if field_index >= len(self._ctx.item_fields):
            return self._commit_item(state)

        leaf = self._sequence.children[field_index]
        status = leaf.apply_input(value, state)
        if status == PatternStatus.FAILURE:
            return PatternStatus.WAITING_FOR_INPUT

        if collection_field_index(state) >= len(self._ctx.item_fields):
            return self._commit_item(state)
        return self.run(state, None)

    def _commit_item(self, state: BaseState) -> PatternStatus:
        items = get_collection_items(state, self._ctx.collection_key)
        draft = collection_draft(state)
        edit_index = collection_edit_index(state)
        item_index = edit_index if edit_index is not None else len(items)

        if edit_index is None:
            items.append(dict(draft))
        else:
            items[edit_index] = dict(draft)

        set_collection_items(state, self._ctx.collection_key, items)
        leave_item_scope(state, self._ctx.step, item_index, context=self._ctx.context_engine)
        clear_collection_session(state)
        emit_wizard_event(
            self._ctx.emit,
            self._ctx.wizard_name,
            WizardEventType.COLLECTION_ITEM_SAVED,
            collection_key=self._ctx.collection_key,
            index=edit_index if edit_index is not None else len(items) - 1,
            item=dict(draft),
        )
        set_collection_phase(state, "menu")
        return PatternStatus.FAILURE