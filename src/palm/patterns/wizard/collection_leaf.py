"""
WizardCollectionLeaf — repeatable item collection with per-item scopes.
"""

from __future__ import annotations

from typing import Any

from palm.core.behavior_tree import InteractiveLeaf, PatternStatus
from palm.core.context import BaseState, ContextEngine
from palm.patterns.wizard.collection import CollectionFieldConfig
from palm.patterns.wizard.collection_state import (
    ACTION_ADD,
    ACTION_DONE,
    clear_collection_session,
    collection_draft,
    collection_edit_index,
    collection_field_index,
    collection_phase,
    collection_remove_index,
    enter_field_scope,
    ensure_scope,
    leave_field_scope,
    field_as_step,
    format_item_label,
    get_collection_items,
    item_scope_name,
    leave_item_scope,
    normalize_optional_field_value,
    set_collection_draft,
    set_collection_edit_index,
    set_collection_field_index,
    set_collection_items,
    set_collection_phase,
    set_collection_remove_index,
)
from palm.patterns.wizard.config import WizardStepConfig
from palm.patterns.wizard.events import WizardEventType
from palm.patterns.wizard.keys import WizardKeys
from palm.patterns.wizard.state import enrich_prompt_bundle, enter_step, leave_step
from palm.patterns.wizard.step_leaf import EventEmitter
from palm.patterns.wizard.validation import (
    choice_selection_error,
    clear_validation_feedback,
    prepare_step_input,
    publish_validation_feedback,
    resolve_choice_value,
    validate_collected_answers,
    validate_step_input,
)


class WizardCollectionLeaf(InteractiveLeaf):
    """Build a list of structured items with add, edit, remove, and done actions."""

    def __init__(
        self,
        step: WizardStepConfig,
        *,
        wizard_name: str,
        step_index: int,
        emit: EventEmitter | None = None,
        context_engine: ContextEngine | None = None,
    ) -> None:
        super().__init__(step.slug)
        self._step = step
        self._wizard_name = wizard_name
        self._step_index = step_index
        self._emit = emit
        self._context = context_engine
        self._collection_key = step.collection_key or step.slug
        self._fields = step.item_fields
        self._min_items = step.min_items

    def _tick_impl(self, state: BaseState) -> PatternStatus:
        key = self.input_key()
        if state.has(key):
            value = state.get(key)
            state.delete(key)
            return self._handle_input(value, state)
        return self._request_input(state)

    def _request_input(self, state: BaseState) -> PatternStatus:
        phase = collection_phase(state)
        if phase == "field":
            return self._request_field_input(state)
        if phase == "remove_confirm":
            return self._request_remove_confirm(state)
        return self._request_menu(state)

    def _handle_input(self, value: Any, state: BaseState) -> PatternStatus:
        phase = collection_phase(state)
        if phase == "field":
            return self._handle_field_input(value, state)
        if phase == "remove_confirm":
            return self._handle_remove_confirm(value, state)
        return self._handle_menu_input(value, state)

    def _request_menu(self, state: BaseState) -> PatternStatus:
        ensure_scope(state, self._step.slug, step=self._step, context=self._context)
        items = get_collection_items(state, self._collection_key)
        choices, actions = self._menu_choices(items)
        bundle = self._prompt_bundle(
            state,
            prompt=self._step.prompt,
            field_type="choice",
            choices=choices,
            extra={
                "step_kind": "collection",
                "collection_phase": "menu",
                "collection_key": self._collection_key,
                "collection_items": items,
                "collection_actions": actions,
            },
        )
        return self._activate(state, bundle)

    def _handle_menu_input(self, value: Any, state: BaseState) -> PatternStatus:
        items = get_collection_items(state, self._collection_key)
        choices, actions = self._menu_choices(items)
        resolved = resolve_choice_value(value, choices)
        if resolved is None:
            return self._fail(
                state,
                (choice_selection_error(value, choices),),
                prompt_bundle=self._prompt_bundle(
                    state,
                    prompt=self._step.prompt,
                    field_type="choice",
                    choices=choices,
                    extra={
                        "step_kind": "collection",
                        "collection_phase": "menu",
                        "collection_items": items,
                    },
                ),
            )

        action = actions[choices.index(resolved)]
        if action == ACTION_ADD:
            return self._start_item(state, edit_index=None)
        if action == ACTION_DONE:
            return self._finish_collection(state, items)
        if isinstance(action, tuple) and action[0] == "edit":
            return self._start_item(state, edit_index=action[1])
        if isinstance(action, tuple) and action[0] == "remove":
            return self._start_remove_confirm(state, index=action[1])
        return self._request_menu(state)

    def _start_item(self, state: BaseState, *, edit_index: int | None) -> PatternStatus:
        items = get_collection_items(state, self._collection_key)
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
        ensure_scope(state, self._step.slug, step=self._step, context=self._context)
        ensure_scope(state, item_scope_name(index), context=self._context)
        return self._request_field_input(state)

    def _request_field_input(self, state: BaseState) -> PatternStatus:
        field_index = collection_field_index(state)
        if field_index >= len(self._fields):
            return self._commit_item(state)

        field = self._fields[field_index]
        edit_index = collection_edit_index(state)
        item_index = edit_index if edit_index is not None else len(
            get_collection_items(state, self._collection_key),
        )
        enter_field_scope(state, self._step, field, item_index, context=self._context)

        draft = collection_draft(state)
        progress = f"Item field {field_index + 1}/{len(self._fields)}"
        if edit_index is not None:
            progress = f"Editing item #{edit_index + 1} — {progress}"

        bundle = self._prompt_bundle(
            state,
            prompt=field.prompt,
            field_type=field.field_type,
            choices=list(field.choices),
            title=field.title,
            extra={
                "step_kind": "collection",
                "collection_phase": "field",
                "collection_field": field.slug,
                "collection_draft": draft,
                "collection_progress": progress,
            },
        )
        return self._activate(state, bundle)

    def _handle_field_input(self, value: Any, state: BaseState) -> PatternStatus:
        field_index = collection_field_index(state)
        if field_index >= len(self._fields):
            return self._commit_item(state)

        field = self._fields[field_index]
        step_field = field_as_step(field)
        value = normalize_optional_field_value(field, value)
        value, choice_error = prepare_step_input(state, step_field, value)
        if choice_error is not None:
            return self._fail(
                state,
                choice_error.errors,
                prompt_bundle=self._prompt_bundle(
                    state,
                    prompt=field.prompt,
                    field_type=field.field_type,
                    choices=list(field.choices),
                    title=field.title,
                    extra={
                        "step_kind": "collection",
                        "collection_phase": "field",
                        "collection_field": field.slug,
                        "collection_draft": collection_draft(state),
                    },
                ),
            )
        validation = validate_step_input(state, step_field, value)
        if not validation.ok:
            return self._fail(
                state,
                validation.errors,
                prompt_bundle=self._prompt_bundle(
                    state,
                    prompt=field.prompt,
                    field_type=field.field_type,
                    choices=list(field.choices),
                    title=field.title,
                    extra={
                        "step_kind": "collection",
                        "collection_phase": "field",
                        "collection_field": field.slug,
                        "collection_draft": collection_draft(state),
                    },
                ),
            )

        edit_index = collection_edit_index(state)
        item_index = edit_index if edit_index is not None else len(
            get_collection_items(state, self._collection_key),
        )
        leave_field_scope(state, field, item_index, context=self._context)
        draft = collection_draft(state)
        if value is None:
            draft.pop(field.slug, None)
        else:
            draft[field.slug] = value
        set_collection_draft(state, draft)
        set_collection_field_index(state, field_index + 1)
        clear_validation_feedback(state)
        self._fire(
            WizardEventType.INPUT_RECEIVED,
            slug=f"{self._step.slug}.{field.slug}",
            value=value,
            step_index=self._step_index,
        )
        if field_index + 1 >= len(self._fields):
            return self._commit_item(state)
        return self._request_field_input(state)

    def _commit_item(self, state: BaseState) -> PatternStatus:
        items = get_collection_items(state, self._collection_key)
        draft = collection_draft(state)
        edit_index = collection_edit_index(state)
        item_index = edit_index if edit_index is not None else len(items)

        if edit_index is None:
            items.append(dict(draft))
        else:
            items[edit_index] = dict(draft)

        set_collection_items(state, self._collection_key, items)
        leave_item_scope(state, self._step, item_index, context=self._context)
        clear_collection_session(state)
        self._fire(
            WizardEventType.COLLECTION_ITEM_SAVED,
            collection_key=self._collection_key,
            index=edit_index if edit_index is not None else len(items) - 1,
            item=dict(draft),
        )
        return self._request_menu(state)

    def _start_remove_confirm(self, state: BaseState, *, index: int) -> PatternStatus:
        items = get_collection_items(state, self._collection_key)
        label = format_item_label(items[index], index=index)
        set_collection_remove_index(state, index)
        set_collection_phase(state, "remove_confirm")
        bundle = self._prompt_bundle(
            state,
            prompt=f"Remove '{label}'? Type yes to confirm or no to cancel.",
            field_type="confirm",
            title="Confirm removal",
            extra={
                "step_kind": "collection",
                "collection_phase": "remove_confirm",
                "collection_remove_index": index,
            },
        )
        return self._activate(state, bundle)

    def _request_remove_confirm(self, state: BaseState) -> PatternStatus:
        index = collection_remove_index(state)
        if index is None:
            set_collection_phase(state, "menu")
            return self._request_menu(state)
        items = get_collection_items(state, self._collection_key)
        label = format_item_label(items[index], index=index)
        bundle = self._prompt_bundle(
            state,
            prompt=f"Remove '{label}'? Type yes to confirm or no to cancel.",
            field_type="confirm",
            title="Confirm removal",
            extra={
                "step_kind": "collection",
                "collection_phase": "remove_confirm",
            },
        )
        return self._activate(state, bundle)

    def _handle_remove_confirm(self, value: Any, state: BaseState) -> PatternStatus:
        if value in (False, "no", "No", "NO"):
            clear_collection_session(state)
            return self._request_menu(state)
        if value not in (True, "yes", "Yes", "YES"):
            return self._fail(
                state,
                ("Please answer yes or no.",),
                prompt_bundle=self._prompt_bundle(
                    state,
                    prompt="Remove this item? Type yes or no.",
                    field_type="confirm",
                    title="Confirm removal",
                    extra={"step_kind": "collection", "collection_phase": "remove_confirm"},
                ),
            )

        index = collection_remove_index(state)
        if index is None:
            return self._request_menu(state)

        items = get_collection_items(state, self._collection_key)
        if 0 <= index < len(items):
            removed = items.pop(index)
            set_collection_items(state, self._collection_key, items)
            self._fire(
                WizardEventType.COLLECTION_ITEM_REMOVED,
                collection_key=self._collection_key,
                index=index,
                item=removed,
            )
        clear_collection_session(state)
        return self._request_menu(state)

    def _finish_collection(self, state: BaseState, items: list[dict[str, Any]]) -> PatternStatus:
        if len(items) < self._min_items:
            message = (
                f"Add at least {self._min_items} item(s) before continuing "
                f"({len(items)} so far)."
            )
            choices, _actions = self._menu_choices(items)
            return self._fail(
                state,
                (message,),
                prompt_bundle=self._prompt_bundle(
                    state,
                    prompt=self._step.prompt,
                    field_type="choice",
                    choices=choices,
                    extra={
                        "step_kind": "collection",
                        "collection_phase": "menu",
                        "collection_items": items,
                    },
                ),
            )

        from palm.patterns.wizard.state import get_answers

        answers = get_answers(state)
        answers[self._collection_key] = items
        validation = validate_collected_answers(state, answers)
        if not validation.ok:
            choices, _actions = self._menu_choices(items)
            return self._fail(
                state,
                validation.errors,
                prompt_bundle=self._prompt_bundle(
                    state,
                    prompt=self._step.prompt,
                    field_type="choice",
                    choices=choices,
                    extra={
                        "step_kind": "collection",
                        "collection_phase": "menu",
                        "collection_items": items,
                    },
                ),
            )

        from palm.patterns.wizard.state import persist_step_answer

        persist_step_answer(state, self._collection_key, items)
        clear_collection_session(state)
        leave_step(state, self._step.slug, context=self._context)
        state.delete(WizardKeys.ACTIVE_PROMPT)
        clear_validation_feedback(state)
        self._fire(
            WizardEventType.COLLECTION_COMPLETED,
            collection_key=self._collection_key,
            count=len(items),
        )
        return PatternStatus.SUCCESS

    def _menu_choices(self, items: list[dict[str, Any]]) -> tuple[list[str], list[Any]]:
        choices: list[str] = ["Add a new item"]
        actions: list[Any] = [ACTION_ADD]
        for index, item in enumerate(items):
            label = format_item_label(item, index=index)
            choices.append(f"Edit #{index + 1}: {label}")
            actions.append(("edit", index))
            choices.append(f"Remove #{index + 1}: {label}")
            actions.append(("remove", index))
        done_label = "Continue to summary"
        if len(items) < self._min_items:
            done_label = f"Continue to summary (need {self._min_items - len(items)} more)"
        choices.append(done_label)
        actions.append(ACTION_DONE)
        return choices, actions

    def _prompt_bundle(
        self,
        state: BaseState,
        *,
        prompt: str,
        field_type: str,
        choices: list[str] | None = None,
        title: str | None = None,
        extra: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        bundle: dict[str, Any] = {
            "wizard": self._wizard_name,
            "slug": self._step.slug,
            "title": title or self._step.title,
            "prompt": prompt,
            "field_type": field_type,
            "choices": list(choices or ()),
            "step_index": self._step_index,
            "input_key": self.input_key(),
        }
        if extra:
            bundle.update(extra)
        return enrich_prompt_bundle(state, bundle, context=self._context)

    def _activate(self, state: BaseState, bundle: dict[str, Any]) -> PatternStatus:
        state.set(self.prompt_key(), bundle)
        state.set(WizardKeys.ACTIVE_PROMPT, bundle)
        state.set(WizardKeys.CURRENT_STEP, self._step.slug)
        state.set(WizardKeys.STEP_INDEX, self._step_index)
        self._fire(
            WizardEventType.STEP_STARTED,
            slug=self._step.slug,
            title=bundle.get("title", self._step.title),
            step_index=self._step_index,
            step_kind="collection",
        )
        return PatternStatus.WAITING_FOR_INPUT

    def _fail(
        self,
        state: BaseState,
        errors: tuple[str, ...],
        *,
        prompt_bundle: dict[str, Any],
    ) -> PatternStatus:
        publish_validation_feedback(
            state,
            errors,
            prompt_bundle=prompt_bundle,
            prompt_key=self.prompt_key(),
        )
        self._fire(
            WizardEventType.VALIDATION_FAILED,
            slug=self._step.slug,
            errors=list(errors),
        )
        return PatternStatus.WAITING_FOR_INPUT

    def _fire(self, event_type: str, **payload: Any) -> None:
        if self._emit is not None:
            payload.setdefault("wizard", self._wizard_name)
            self._emit(event_type, payload)