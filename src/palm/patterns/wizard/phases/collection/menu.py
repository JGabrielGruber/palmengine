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
from palm.patterns.wizard.phases._base import WizardPhaseContext
from palm.patterns.wizard.phases.bt import phase_transition
from palm.patterns.wizard.phases.collection._base import (
    CollectionPhaseLeaf,
    begin_item_session,
    step_collection_key,
    step_label_field,
)
from palm.patterns.wizard.state import get_answers, leave_step, persist_step_answer
from palm.patterns.wizard.validation import (
    choice_selection_error,
    clear_validation_feedback,
    resolve_choice_value,
    validate_collected_answers,
)


class CollectionMenuPhase(CollectionPhaseLeaf):
    phase_key = "menu"

    def _request_input(self, state: BaseState) -> PatternStatus:
        ensure_scope(state, self._ctx.step.slug, step=self._ctx.step, context=self._ctx.context_engine)
        items = get_collection_items(state, step_collection_key(self._ctx))
        choices, actions = self._menu_choices(items)
        bundle = self._prompt_bundle(
            state,
            prompt=self._menu_prompt(items),
            field_type="choice",
            choices=choices,
            extra={
                "collection_phase": "menu",
                "collection_key": step_collection_key(self._ctx),
                "collection_items": items,
                "collection_actions": actions,
            },
        )
        return self._activate(state, bundle)

    def _handle_input(self, value: Any, state: BaseState) -> PatternStatus:
        items = get_collection_items(state, step_collection_key(self._ctx))
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
            begin_item_session(state, self._ctx, edit_index=None)
            set_collection_phase(state, "field")
            return phase_transition()
        if action == ACTION_DONE:
            return self._finish_collection(state, items)
        if action == ACTION_EDIT_SELECT:
            set_collection_select_action(state, "edit")
            set_collection_phase(state, "select_item")
            return phase_transition()
        if action == ACTION_REMOVE_SELECT:
            set_collection_select_action(state, "remove")
            set_collection_phase(state, "select_item")
            return phase_transition()
        return self._request_input(state)

    def _finish_collection(self, state: BaseState, items: list[dict[str, Any]]) -> PatternStatus:
        if len(items) < self._ctx.step.min_items:
            message = (
                f"Add at least {self._ctx.step.min_items} item(s) before continuing "
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
        answers[step_collection_key(self._ctx)] = items
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

        persist_step_answer(state, step_collection_key(self._ctx), items)
        clear_collection_session(state)
        leave_step(state, self._ctx.step.slug, context=self._ctx.context_engine)
        state.delete(WizardKeys.ACTIVE_PROMPT)
        clear_validation_feedback(state)
        emit_wizard_event(
            self._ctx.emit,
            self._ctx.wizard_name,
            WizardEventType.COLLECTION_COMPLETED,
            collection_key=step_collection_key(self._ctx),
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
        if len(items) < self._ctx.step.min_items:
            done_label = f"Continue to summary (need {self._ctx.step.min_items - len(items)} more)"
        choices.append(done_label)
        actions.append(ACTION_DONE)
        return choices, actions

    def _menu_prompt(self, items: list[dict[str, Any]]) -> str:
        base = self._ctx.step.prompt
        if not items:
            return base
        listing = format_numbered_item_list(
            items,
            label_field=step_label_field(self._ctx),
            item_fields=self._ctx.step.item_fields,
        )
        return f"{base}\n\nCurrent items:\n{listing}"


def build_menu_phase(ctx: WizardPhaseContext) -> CollectionMenuPhase:
    return CollectionMenuPhase(ctx)