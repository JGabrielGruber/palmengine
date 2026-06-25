"""Collection remove phase — confirm item deletion."""

from __future__ import annotations

from typing import Any

from palm.core.behavior_tree.base_pattern import PatternStatus
from palm.core.context import BaseState
from palm.patterns.wizard.flow.collection.state import (
    clear_collection_session,
    collection_remove_index,
    format_item_label,
    get_collection_items,
    set_collection_items,
    set_collection_phase,
)
from palm.patterns.wizard.bindings.events.types import WizardEventType
from palm.patterns.wizard.bindings.events.support import emit_wizard_event
from palm.patterns.wizard.flow.phases._base import WizardPhaseContext, is_affirmative
from palm.patterns.wizard.bindings.behavior_tree.bt import phase_transition
from palm.patterns.wizard.flow.collection.phases._base import (
    CollectionPhaseLeaf,
    step_collection_key,
    step_label_field,
)


class CollectionRemovePhase(CollectionPhaseLeaf):
    phase_key = "remove_confirm"

    def _request_input(self, state: BaseState) -> PatternStatus:
        index = collection_remove_index(state)
        if index is None:
            set_collection_phase(state, "menu")
            return phase_transition()

        items = get_collection_items(state, step_collection_key(self._ctx))
        label = format_item_label(
            items[index],
            index=index,
            label_field=step_label_field(self._ctx),
            item_fields=self._ctx.step.item_fields,
        )
        bundle = self._prompt_bundle(
            state,
            prompt=f"Remove '{label}'? Type yes to confirm or no to cancel.",
            field_type="confirm",
            title="Confirm removal",
            extra={"collection_phase": "remove_confirm", "collection_remove_index": index},
        )
        return self._activate(state, bundle)

    def _handle_input(self, value: Any, state: BaseState) -> PatternStatus:
        if value in (False, "no", "No", "NO"):
            clear_collection_session(state)
            set_collection_phase(state, "menu")
            return phase_transition()

        if not is_affirmative(value):
            return self._fail(
                state,
                ("Please answer yes or no.",),
                prompt_bundle=self._prompt_bundle(
                    state,
                    prompt="Remove this item? Type yes or no.",
                    field_type="confirm",
                    title="Confirm removal",
                    extra={"collection_phase": "remove_confirm"},
                ),
            )

        index = collection_remove_index(state)
        if index is None:
            set_collection_phase(state, "menu")
            return phase_transition()

        items = get_collection_items(state, step_collection_key(self._ctx))
        if 0 <= index < len(items):
            removed = items.pop(index)
            set_collection_items(state, step_collection_key(self._ctx), items)
            emit_wizard_event(
                self._ctx.emit,
                self._ctx.wizard_name,
                WizardEventType.COLLECTION_ITEM_REMOVED,
                collection_key=step_collection_key(self._ctx),
                index=index,
                item=removed,
            )
        clear_collection_session(state)
        set_collection_phase(state, "menu")
        return phase_transition()


def build_remove_phase(ctx: WizardPhaseContext) -> CollectionRemovePhase:
    return CollectionRemovePhase(ctx)