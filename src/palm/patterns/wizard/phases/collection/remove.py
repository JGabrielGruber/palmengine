"""Collection remove phase — confirm item deletion."""

from __future__ import annotations

from typing import Any

from palm.core.behavior_tree.base_pattern import PatternStatus
from palm.core.context import BaseState
from palm.patterns.wizard.collection_state import (
    clear_collection_session,
    collection_remove_index,
    format_item_label,
    get_collection_items,
    set_collection_items,
    set_collection_phase,
    set_collection_remove_index,
)
from palm.patterns.wizard.events import WizardEventType
from palm.patterns.wizard.leaf_support import emit_wizard_event
from palm.patterns.wizard.phases._base import is_affirmative
from palm.patterns.wizard.phases.collection._base import CollectionPhaseContext, CollectionPhaseLeaf


class CollectionRemovePhase(CollectionPhaseLeaf):
    phase_key = "remove_confirm"

    def start_confirm(self, state: BaseState, *, index: int) -> PatternStatus:
        set_collection_remove_index(state, index)
        set_collection_phase(state, "remove_confirm")
        return self.run(state, None)

    def _request_input(self, state: BaseState) -> PatternStatus:
        index = collection_remove_index(state)
        if index is None:
            set_collection_phase(state, "menu")
            return PatternStatus.FAILURE

        items = get_collection_items(state, self._ctx.collection_key)
        label = format_item_label(
            items[index],
            index=index,
            label_field=self._ctx.label_field,
            item_fields=self._ctx.item_fields,
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
            return PatternStatus.FAILURE

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
            return PatternStatus.FAILURE

        items = get_collection_items(state, self._ctx.collection_key)
        if 0 <= index < len(items):
            removed = items.pop(index)
            set_collection_items(state, self._ctx.collection_key, items)
            emit_wizard_event(
                self._ctx.emit,
                self._ctx.wizard_name,
                WizardEventType.COLLECTION_ITEM_REMOVED,
                collection_key=self._ctx.collection_key,
                index=index,
                item=removed,
            )
        clear_collection_session(state)
        set_collection_phase(state, "menu")
        return PatternStatus.FAILURE