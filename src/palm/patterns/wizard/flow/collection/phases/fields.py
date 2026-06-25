"""Collection fields phase — BT sequence for per-item field collection."""

from __future__ import annotations

from typing import Any

from palm.core.behavior_tree import LeafNode, PatternStatus, SequenceNode
from palm.core.context import BaseState
from palm.patterns.wizard.flow.collection.config import CollectionFieldConfig
from palm.patterns.wizard.flow.collection.state import (
    clear_collection_session,
    collection_draft,
    collection_edit_index,
    collection_field_index,
    enter_field_scope,
    field_as_step,
    get_collection_items,
    leave_field_scope,
    leave_item_scope,
    normalize_optional_field_value,
    set_collection_draft,
    set_collection_field_index,
    set_collection_items,
    set_collection_phase,
)
from palm.patterns.wizard.bindings.events.types import WizardEventType
from palm.patterns.wizard.bindings.context.keys import WizardKeys
from palm.patterns.wizard.bindings.events.support import build_prompt_bundle, emit_wizard_event
from palm.patterns.wizard.flow.phases._base import WizardPhaseContext
from palm.patterns.wizard.bindings.behavior_tree.bt import phase_transition
from palm.patterns.wizard.flow.collection.phases._base import (
    CollectionPhaseLeaf,
    step_collection_key,
)
from palm.patterns.wizard.flow.validation import (
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
        ctx: WizardPhaseContext,
    ) -> None:
        super().__init__(f"{ctx.step.slug}.{field.slug}")
        self._field = field
        self._ctx = ctx

    def apply_input(self, value: Any, state: BaseState) -> PatternStatus:
        field_index = collection_field_index(state)
        if field_index >= len(self._ctx.step.item_fields):
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
            else len(get_collection_items(state, step_collection_key(self._ctx)))
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
        if field_index >= len(self._ctx.step.item_fields):
            return PatternStatus.SUCCESS
        if self._ctx.step.item_fields[field_index].slug != self._field.slug:
            return PatternStatus.FAILURE

        edit_index = collection_edit_index(state)
        item_index = (
            edit_index
            if edit_index is not None
            else len(get_collection_items(state, step_collection_key(self._ctx)))
        )
        enter_field_scope(
            state,
            self._ctx.step,
            self._field,
            item_index,
            context=self._ctx.context_engine,
        )

        draft = collection_draft(state)
        progress = f"Item field {field_index + 1}/{len(self._ctx.step.item_fields)}"
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


def build_field_sequence(ctx: WizardPhaseContext) -> SequenceNode:
    children = [CollectionFieldLeaf(field, ctx=ctx) for field in ctx.step.item_fields]
    return SequenceNode(f"{ctx.step.slug}_fields", children=children)


class CollectionFieldsPhase(CollectionPhaseLeaf):
    phase_key = "field"

    def __init__(self, ctx: WizardPhaseContext) -> None:
        super().__init__(ctx)
        self._sequence = build_field_sequence(ctx)
        self._session_id = 0

    def _maybe_reset_sequence(self, state: BaseState) -> None:
        session_id = int(state.get(WizardKeys.COLLECTION_SESSION_ID, 0))
        if session_id != self._session_id:
            self._session_id = session_id
            self._sequence.reset()

    def _request_input(self, state: BaseState) -> PatternStatus:
        self._maybe_reset_sequence(state)
        field_index = collection_field_index(state)
        if field_index >= len(self._ctx.step.item_fields):
            return self._commit_item(state)

        leaf = self._sequence.children[field_index]
        leaf.tick(state)
        bundle = state.get(f"__bt_prompt__:{self._ctx.step.slug}")
        if not isinstance(bundle, dict):
            return PatternStatus.FAILURE
        return self._activate(state, dict(bundle))

    def _handle_input(self, value: Any, state: BaseState) -> PatternStatus:
        field_index = collection_field_index(state)
        if field_index >= len(self._ctx.step.item_fields):
            return self._commit_item(state)

        leaf = self._sequence.children[field_index]
        status = leaf.apply_input(value, state)
        if status == PatternStatus.FAILURE:
            return PatternStatus.WAITING_FOR_INPUT

        if collection_field_index(state) >= len(self._ctx.step.item_fields):
            return self._commit_item(state)
        return self._request_input(state)

    def _commit_item(self, state: BaseState) -> PatternStatus:
        items = get_collection_items(state, step_collection_key(self._ctx))
        draft = collection_draft(state)
        edit_index = collection_edit_index(state)
        item_index = edit_index if edit_index is not None else len(items)

        if edit_index is None:
            items.append(dict(draft))
        else:
            items[edit_index] = dict(draft)

        set_collection_items(state, step_collection_key(self._ctx), items)
        leave_item_scope(state, self._ctx.step, item_index, context=self._ctx.context_engine)
        clear_collection_session(state)
        emit_wizard_event(
            self._ctx.emit,
            self._ctx.wizard_name,
            WizardEventType.COLLECTION_ITEM_SAVED,
            collection_key=step_collection_key(self._ctx),
            index=edit_index if edit_index is not None else len(items) - 1,
            item=dict(draft),
        )
        set_collection_phase(state, "menu")
        return phase_transition()


def build_fields_phase(ctx: WizardPhaseContext) -> CollectionFieldsPhase:
    return CollectionFieldsPhase(ctx)