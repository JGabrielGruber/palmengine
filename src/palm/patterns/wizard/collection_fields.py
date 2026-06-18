"""
Collection field sequence — behavior-tree driven per-item field collection.

Each field in a collection item is a dedicated leaf in a :class:`SequenceNode`,
replacing manual field-index orchestration inside :class:`WizardCollectionLeaf`.
"""

from __future__ import annotations

from typing import Any

from palm.core.behavior_tree import LeafNode, PatternStatus, SequenceNode
from palm.core.context import BaseState, ContextEngine
from palm.patterns.wizard.collection import CollectionFieldConfig
from palm.patterns.wizard.collection_state import (
    collection_draft,
    collection_edit_index,
    collection_field_index,
    enter_field_scope,
    field_as_step,
    get_collection_items,
    leave_field_scope,
    normalize_optional_field_value,
    set_collection_draft,
    set_collection_field_index,
)
from palm.patterns.wizard.config import WizardStepConfig
from palm.patterns.wizard.events import WizardEventType
from palm.patterns.wizard.leaf_support import build_prompt_bundle, emit_wizard_event
from palm.patterns.wizard.step_leaf import EventEmitter
from palm.patterns.wizard.validation import (
    choice_selection_error,
    prepare_step_input,
    publish_validation_feedback,
    validate_step_input,
)


class CollectionFieldLeaf(LeafNode):
    """Collect one field value for the active collection item draft."""

    def __init__(
        self,
        field: CollectionFieldConfig,
        *,
        step: WizardStepConfig,
        wizard_name: str,
        step_index: int,
        collection_key: str,
        emit: EventEmitter | None = None,
        context_engine: ContextEngine | None = None,
    ) -> None:
        super().__init__(f"{step.slug}.{field.slug}")
        self._field = field
        self._step = step
        self._wizard_name = wizard_name
        self._step_index = step_index
        self._collection_key = collection_key
        self._emit = emit
        self._context = context_engine

    def apply_input(self, value: Any, state: BaseState) -> PatternStatus:
        """Validate and store input for this field, returning terminal status."""
        field_index = collection_field_index(state)
        if field_index >= len(self._step.item_fields):
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
            else len(get_collection_items(state, self._collection_key))
        )
        leave_field_scope(state, self._field, item_index, context=self._context)

        draft = collection_draft(state)
        if value is None:
            draft.pop(self._field.slug, None)
        else:
            draft[self._field.slug] = value
        set_collection_draft(state, draft)
        set_collection_field_index(state, field_index + 1)
        emit_wizard_event(
            self._emit,
            self._wizard_name,
            WizardEventType.INPUT_RECEIVED,
            slug=self.name,
            value=value,
            step_index=self._step_index,
        )
        return PatternStatus.SUCCESS

    def _tick_impl(self, state: BaseState) -> PatternStatus:
        field_index = collection_field_index(state)
        if field_index >= len(self._step.item_fields):
            return PatternStatus.SUCCESS

        expected = self._step.item_fields[field_index]
        if expected.slug != self._field.slug:
            return PatternStatus.FAILURE

        edit_index = collection_edit_index(state)
        item_index = (
            edit_index
            if edit_index is not None
            else len(get_collection_items(state, self._collection_key))
        )
        enter_field_scope(state, self._step, self._field, item_index, context=self._context)

        draft = collection_draft(state)
        progress = f"Item field {field_index + 1}/{len(self._step.item_fields)}"
        if edit_index is not None:
            progress = f"Editing item #{edit_index + 1} — {progress}"

        bundle = build_prompt_bundle(
            state,
            wizard_name=self._wizard_name,
            step=self._step,
            step_index=self._step_index,
            context=self._context,
            prompt=self._field.prompt,
            field_type=self._field.field_type,
            choices=list(self._field.choices),
            title=self._field.title,
            collection_phase="field",
            collection_field=self._field.slug,
            collection_draft=draft,
            collection_progress=progress,
        )
        state.set(self._prompt_key(), bundle)
        return PatternStatus.RUNNING

    def _fail(self, state: BaseState, errors: tuple[str, ...]) -> PatternStatus:
        publish_validation_feedback(
            state,
            errors,
            prompt_bundle=build_prompt_bundle(
                state,
                wizard_name=self._wizard_name,
                step=self._step,
                step_index=self._step_index,
                context=self._context,
                prompt=self._field.prompt,
                field_type=self._field.field_type,
                choices=list(self._field.choices),
                title=self._field.title,
                collection_phase="field",
                collection_field=self._field.slug,
                collection_draft=collection_draft(state),
            ),
            prompt_key=self._prompt_key(),
        )
        return PatternStatus.FAILURE

    def _prompt_key(self) -> str:
        return f"__bt_prompt__:{self._step.slug}"


def build_collection_field_sequence(
    step: WizardStepConfig,
    *,
    wizard_name: str,
    step_index: int,
    collection_key: str,
    emit: EventEmitter | None = None,
    context_engine: ContextEngine | None = None,
) -> SequenceNode:
    """Return a sequence of field leaves for one collection item."""
    children = [
        CollectionFieldLeaf(
            field,
            step=step,
            wizard_name=wizard_name,
            step_index=step_index,
            collection_key=collection_key,
            emit=emit,
            context_engine=context_engine,
        )
        for field in step.item_fields
    ]
    return SequenceNode(f"{step.slug}_fields", children=children)