"""Collection select phase — pick an item to edit or remove."""

from __future__ import annotations

from typing import Any

from palm.core.behavior_tree.base_pattern import PatternStatus
from palm.core.context import BaseState
from palm.patterns.wizard.collection_selection import (
    format_item_preview,
    is_cancel_input,
    item_selection_error,
    item_selection_prompt,
    resolve_item_index,
)
from palm.patterns.wizard.collection_state import (
    collection_select_action,
    get_collection_items,
    set_collection_phase,
    set_collection_remove_index,
    set_collection_select_action,
)
from palm.patterns.wizard.phases.bt import phase_transition
from palm.patterns.wizard.phases.collection._base import (
    CollectionPhaseLeaf,
    begin_item_session,
    step_collection_key,
    step_label_field,
)
from palm.patterns.wizard.phases._base import WizardPhaseContext


class CollectionSelectPhase(CollectionPhaseLeaf):
    phase_key = "select_item"

    def _select_action(self, state: BaseState) -> str:
        action = collection_select_action(state)
        return "remove" if action == "remove" else "edit"

    def _request_input(self, state: BaseState) -> PatternStatus:
        items = get_collection_items(state, step_collection_key(self._ctx))
        if not items:
            set_collection_phase(state, "menu")
            return phase_transition()

        action = self._select_action(state)
        previews = [
            format_item_preview(
                item,
                index=index,
                label_field=step_label_field(self._ctx),
                item_fields=self._ctx.step.item_fields,
            )
            for index, item in enumerate(items)
        ]
        bundle = self._prompt_bundle(
            state,
            prompt=item_selection_prompt(action),
            field_type="text",
            title="Edit item" if action == "edit" else "Remove item",
            extra={
                "collection_phase": "select_item",
                "collection_select_action": action,
                "collection_item_previews": previews,
                "collection_items": items,
            },
        )
        return self._activate(state, bundle)

    def _handle_input(self, value: Any, state: BaseState) -> PatternStatus:
        items = get_collection_items(state, step_collection_key(self._ctx))
        action = self._select_action(state)
        if is_cancel_input(value):
            set_collection_select_action(state, None)
            set_collection_phase(state, "menu")
            return phase_transition()

        index = resolve_item_index(value, items, label_field=step_label_field(self._ctx))
        if index is None:
            return self._fail(
                state,
                (
                    item_selection_error(
                        value,
                        items,
                        label_field=step_label_field(self._ctx),
                        action=action,
                        item_fields=self._ctx.step.item_fields,
                    ),
                ),
                prompt_bundle=self._prompt_bundle(
                    state,
                    prompt=item_selection_prompt(action),
                    field_type="text",
                    title="Edit item" if action == "edit" else "Remove item",
                    extra={
                        "collection_phase": "select_item",
                        "collection_select_action": action,
                        "collection_item_previews": [
                            format_item_preview(
                                item,
                                index=idx,
                                label_field=step_label_field(self._ctx),
                                item_fields=self._ctx.step.item_fields,
                            )
                            for idx, item in enumerate(items)
                        ],
                        "collection_items": items,
                    },
                ),
            )

        set_collection_select_action(state, None)
        if action == "edit":
            begin_item_session(state, self._ctx, edit_index=index)
            set_collection_phase(state, "field")
            return phase_transition()

        set_collection_remove_index(state, index)
        set_collection_phase(state, "remove_confirm")
        return phase_transition()


def build_select_phase(ctx: WizardPhaseContext) -> CollectionSelectPhase:
    return CollectionSelectPhase(ctx)