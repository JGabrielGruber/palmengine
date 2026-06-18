"""Collection phase shared context and leaf base."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from palm.core.behavior_tree import LeafNode, PatternStatus
from palm.core.context import BaseState, ContextEngine
from palm.patterns.wizard.collection import CollectionFieldConfig
from palm.patterns.wizard.collection_selection import default_label_field
from palm.patterns.wizard.config import WizardStepConfig
from palm.patterns.wizard.events import WizardEventType
from palm.patterns.wizard.leaf_support import emit_wizard_event
from palm.patterns.wizard.phases._base import (
    EventEmitter,
    WizardPhaseContext,
    activate_prompt,
    build_phase_prompt,
    consume_wizard_input,
    wizard_prompt_key,
)
from palm.patterns.wizard.state import enrich_prompt_bundle
from palm.patterns.wizard.validation import publish_validation_feedback


@dataclass(frozen=True)
class CollectionPhaseContext:
    wizard_name: str
    step_index: int
    step: WizardStepConfig
    emit: EventEmitter | None
    context_engine: ContextEngine | None
    collection_key: str
    item_fields: tuple[CollectionFieldConfig, ...]
    min_items: int
    label_field: str | None

    @classmethod
    def from_wizard(cls, ctx: WizardPhaseContext) -> CollectionPhaseContext:
        return cls(
            wizard_name=ctx.wizard_name,
            step_index=ctx.step_index,
            step=ctx.step,
            emit=ctx.emit,
            context_engine=ctx.context_engine,
            collection_key=ctx.step.collection_key or ctx.step.slug,
            item_fields=ctx.step.item_fields,
            min_items=ctx.step.min_items,
            label_field=default_label_field(ctx.step.item_fields, ctx.step.label_field),
        )


class CollectionPhaseLeaf(LeafNode):
    """Base leaf for one collection sub-phase routed by ``CollectionPhaseRouter``."""

    phase_key: str = "menu"

    def __init__(self, ctx: CollectionPhaseContext) -> None:
        super().__init__(f"{ctx.step.slug}:{self.phase_key}")
        self._ctx = ctx

    def run(self, state: BaseState, pending: Any | None) -> PatternStatus:
        if pending is not None:
            return self._handle_input(pending, state)
        return self._request_input(state)

    def _tick_impl(self, state: BaseState) -> PatternStatus:
        pending = consume_wizard_input(state, self._ctx.step.slug)
        return self.run(state, pending)

    def _request_input(self, state: BaseState) -> PatternStatus:
        raise NotImplementedError

    def _handle_input(self, value: Any, state: BaseState) -> PatternStatus:
        raise NotImplementedError

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
            "input_key": f"__bt_input__:{self._ctx.step.slug}",
        }
        if extra:
            bundle.update(extra)
        return enrich_prompt_bundle(state, bundle, context=self._ctx.context_engine)

    def _activate(self, state: BaseState, bundle: dict[str, Any]) -> PatternStatus:
        activate_prompt(
            state,
            ctx=WizardPhaseContext(
                wizard_name=self._ctx.wizard_name,
                step_index=self._ctx.step_index,
                step=self._ctx.step,
                emit=self._ctx.emit,
                context_engine=self._ctx.context_engine,
            ),
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