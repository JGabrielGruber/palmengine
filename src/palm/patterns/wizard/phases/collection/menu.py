"""Collection menu phase — add, edit, remove, or finish."""

from __future__ import annotations

from typing import Any

from palm.core.behavior_tree.base_pattern import PatternStatus
from palm.core.context import BaseState
from palm.patterns.wizard.collection_selection import format_numbered_item_list
from palm.patterns.wizard.collection_state import (
    ACTION_ADD,
    ACTION_DONE,
    ACTION_EDIT_SELECT,
    ACTION_REMOVE_SELECT,
    clear_collection_session,
    ensure_scope,
    get_collection_items,
    set_collection_phase,
    set_collection_select_action,
)
from palm.patterns.wizard.events import WizardEventType
from palm.patterns.wizard.keys import WizardKeys
from palm.patterns.wizard.leaf_support import emit_wizard_event
from palm.patterns.wizard.phases.collection._base import CollectionPhaseContext, CollectionPhaseLeaf
from palm.patterns.wizard.phases.collection.fields import CollectionFieldsPhase
from palm.patterns.wizard.phases.collection.remove import CollectionRemovePhase
from palm.patterns.wizard.phases.collection.select import CollectionSelectPhase
from palm.patterns.wizard.state import get_answers, leave_step, persist_step_answer
from palm.patterns.wizard.validation import (
    choice_selection_error,
    clear_validation_feedback,
    resolve_choice_value,
    validate_collected_answers,
)


class CollectionMenuPhase(CollectionPhaseLeaf):
    phase_key = "menu"

    def __init__(
        self,
        ctx: CollectionPhaseContext,
        *,
        fields_phase: CollectionFieldsPhase,
        select_phase: CollectionSelectPhase,
        remove_phase: CollectionRemovePhase,
    ) -> None:
        super().__init__(ctx)
        self._fields = fields_phase
        self._select = select_phase
        self._remove = remove_phase

    def _request_input(self, state: BaseState) -> PatternStatus:
        ensure_scope(state, self._ctx.step.slug, step=self._ctx.step, context=self._ctx.context_engine)
        items = get_collection_items(state, self._ctx.collection_key)
        choices, actions = self._menu_choices(items)
        bundle = self._prompt_bundle(
            state,
            prompt=self._menu_prompt(items),
            field_type="choice",
            choices=choices,
            extra={
                "collection_phase": "menu",
                "collection_key": self._ctx.collection_key,
                "collection_items": items,
                "collection_actions": actions,
            },
        )
        return self._activate(state, bundle)

    def _handle_input(self, value: Any, state: BaseState) -> PatternStatus:
        items = get_collection_items(state, self._ctx.collection_key)
        choices, actions = self._menu_choices(items)
        resolved = resolve_choice_value(value, choices)
        if resolved is None:
            return self._fail(
                state,
                (choice_selection_error(value, choices),),
                prompt_bundle=self._prompt_bundle(
                    state,
                    prompt=self._menu_prompt(items),
                    field_type="choice",
                    choices=choices,
                    extra={"collection_phase": "menu", "collection_items": items},
                ),
            )

        action = actions[choices.index(resolved)]
        if action == ACTION_ADD:
            return self._fields.start_item(state, edit_index=None)
        if action == ACTION_DONE:
            return self._finish_collection(state, items)
        if action == ACTION_EDIT_SELECT:
            set_collection_select_action(state, "edit")
            set_collection_phase(state, "select_item")
            return self._select.run(state, None)
        if action == ACTION_REMOVE_SELECT:
            set_collection_select_action(state, "remove")
            set_collection_phase(state, "select_item")
            return self._select.run(state, None)
        return self._request_input(state)

    def _finish_collection(self, state: BaseState, items: list[dict[str, Any]]) -> PatternStatus:
        if len(items) < self._ctx.min_items:
            message = (
                f"Add at least {self._ctx.min_items} item(s) before continuing "
                f"({len(items)} so far)."
            )
            choices, _actions = self._menu_choices(items)
            return self._fail(
                state,
                (message,),
                prompt_bundle=self._prompt_bundle(
                    state,
                    prompt=self._menu_prompt(items),
                    field_type="choice",
                    choices=choices,
                    extra={"collection_phase": "menu", "collection_items": items},
                ),
            )

        answers = get_answers(state)
        answers[self._ctx.collection_key] = items
        validation = validate_collected_answers(state, answers)
        if not validation.ok:
            choices, _actions = self._menu_choices(items)
            return self._fail(
                state,
                validation.errors,
                prompt_bundle=self._prompt_bundle(
                    state,
                    prompt=self._menu_prompt(items),
                    field_type="choice",
                    choices=choices,
                    extra={"collection_phase": "menu", "collection_items": items},
                ),
            )

        persist_step_answer(state, self._ctx.collection_key, items)
        clear_collection_session(state)
        leave_step(state, self._ctx.step.slug, context=self._ctx.context_engine)
        state.delete(WizardKeys.ACTIVE_PROMPT)
        clear_validation_feedback(state)
        emit_wizard_event(
            self._ctx.emit,
            self._ctx.wizard_name,
            WizardEventType.COLLECTION_COMPLETED,
            collection_key=self._ctx.collection_key,
            count=len(items),
        )
        return PatternStatus.SUCCESS

    def _menu_choices(self, items: list[dict[str, Any]]) -> tuple[list[str], list[Any]]:
        choices: list[str] = ["Add a new item"]
        actions: list[Any] = [ACTION_ADD]
        if items:
            choices.extend(["Edit an item", "Remove an item"])
            actions.extend([ACTION_EDIT_SELECT, ACTION_REMOVE_SELECT])
        done_label = "Continue to summary"
        if len(items) < self._ctx.min_items:
            done_label = f"Continue to summary (need {self._ctx.min_items - len(items)} more)"
        choices.append(done_label)
        actions.append(ACTION_DONE)
        return choices, actions

    def _menu_prompt(self, items: list[dict[str, Any]]) -> str:
        base = self._ctx.step.prompt
        if not items:
            return base
        listing = format_numbered_item_list(
            items,
            label_field=self._ctx.label_field,
            item_fields=self._ctx.item_fields,
        )
        return f"{base}\n\nCurrent items:\n{listing}"