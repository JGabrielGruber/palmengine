"""Collection phase shared context, session helpers, and interactive leaf base."""

from __future__ import annotations

from typing import Any

from palm.core.behavior_tree import InteractiveLeaf, PatternStatus
from palm.core.context import BaseState
from palm.patterns.wizard.flow.collection.selection import default_label_field
from palm.patterns.wizard.flow.collection.state import (
    ensure_scope,
    get_collection_items,
    item_scope_name,
    set_collection_draft,
    set_collection_edit_index,
    set_collection_field_index,
)
from palm.patterns.wizard.bindings.events.types import WizardEventType
from palm.patterns.wizard.bindings.context.keys import WizardKeys
from palm.patterns.wizard.bindings.events.support import emit_wizard_event
from palm.patterns.wizard.flow.phases._base import (
    WizardPhaseContext,
    activate_prompt,
    wizard_input_key,
    wizard_prompt_key,
)
from palm.patterns.wizard.bindings.context.state import enrich_prompt_bundle
from palm.patterns.wizard.flow.validation import publish_validation_feedback


def step_collection_key(ctx: WizardPhaseContext) -> str:
    return ctx.step.collection_key or ctx.step.slug


def step_label_field(ctx: WizardPhaseContext) -> str | None:
    return default_label_field(ctx.step.item_fields, ctx.step.label_field)


def begin_item_session(
    state: BaseState,
    ctx: WizardPhaseContext,
    *,
    edit_index: int | None,
) -> None:
    """Initialize blackboard state for collecting or editing one collection item."""
    key = step_collection_key(ctx)
    items = get_collection_items(state, key)
    if edit_index is None:
        draft: dict[str, Any] = {}
        index = len(items)
    else:
        draft = dict(items[edit_index])
        index = edit_index

    set_collection_edit_index(state, edit_index)
    set_collection_draft(state, draft)
    set_collection_field_index(state, 0)
    session_id = int(state.get(WizardKeys.COLLECTION_SESSION_ID, 0)) + 1
    state.set(WizardKeys.COLLECTION_SESSION_ID, session_id)
    ensure_scope(state, ctx.step.slug, step=ctx.step, context=ctx.context_engine)
    ensure_scope(state, item_scope_name(index), context=ctx.context_engine)


class CollectionPhaseLeaf(InteractiveLeaf):
    """Base interactive leaf for one routed collection sub-phase."""

    phase_key: str = "menu"

    def __init__(self, ctx: WizardPhaseContext) -> None:
        super().__init__(f"{ctx.step.slug}:{self.phase_key}")
        self._ctx = ctx

    def input_key(self) -> str:
        return wizard_input_key(self._ctx.step.slug)

    def prompt_key(self) -> str:
        return wizard_prompt_key(self._ctx.step.slug)

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
            "wizard": self._ctx.wizard_name,
            "slug": self._ctx.step.slug,
            "title": title or self._ctx.step.title,
            "prompt": prompt,
            "field_type": field_type,
            "choices": list(choices or ()),
            "step_index": self._ctx.step_index,
            "step_kind": "collection",
            "input_key": wizard_input_key(self._ctx.step.slug),
        }
        if extra:
            bundle.update(extra)
        return enrich_prompt_bundle(state, bundle, context=self._ctx.context_engine)

    def _activate(self, state: BaseState, bundle: dict[str, Any]) -> PatternStatus:
        activate_prompt(
            state,
            ctx=self._ctx,
            bundle=bundle,
            event_type=WizardEventType.STEP_STARTED,
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
            prompt_key=wizard_prompt_key(self._ctx.step.slug),
        )
        emit_wizard_event(
            self._ctx.emit,
            self._ctx.wizard_name,
            WizardEventType.VALIDATION_FAILED,
            slug=self._ctx.step.slug,
            errors=list(errors),
        )
        return PatternStatus.WAITING_FOR_INPUT
