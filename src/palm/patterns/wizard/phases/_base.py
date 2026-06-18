"""
Wizard phase foundations — context, input bridge, and shared interactive helpers.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from palm.core.behavior_tree.nodes.leaf.interactive_leaf import InteractiveLeaf
from palm.core.context import BaseState, ContextEngine
from palm.core.resource import ResourceEngine
from palm.patterns.wizard.config import WizardStepConfig
from palm.patterns.wizard.handler import CommitRegistry
from palm.patterns.wizard.keys import WizardKeys
from palm.patterns.wizard.leaf_support import (
    EventEmitter,
    build_prompt_bundle,
    clear_active_prompt,
    emit_wizard_event,
    enter_wizard_step,
    publish_prompt,
    set_step_position,
)

__all__ = [
    "EventEmitter",
    "WizardPhaseContext",
    "activate_prompt",
    "consume_wizard_input",
    "is_affirmative",
    "provide_wizard_input",
    "wizard_input_key",
    "wizard_prompt_key",
]


@dataclass(frozen=True)
class WizardPhaseContext:
    """Shared inputs for building any wizard phase node."""

    wizard_name: str
    step_index: int
    step: WizardStepConfig
    emit: EventEmitter | None = None
    commit_registry: CommitRegistry | None = None
    resource_engine: ResourceEngine | None = None
    context_engine: ContextEngine | None = None


def wizard_input_key(step_slug: str) -> str:
    return f"{InteractiveLeaf.INPUT_KEY_PREFIX}:{step_slug}"


def wizard_prompt_key(step_slug: str) -> str:
    return f"{InteractiveLeaf.PROMPT_KEY_PREFIX}:{step_slug}"


def consume_wizard_input(state: BaseState, step_slug: str) -> Any | None:
    """Read and clear pending operator input for a wizard step."""
    key = wizard_input_key(step_slug)
    if not state.has(key):
        return None
    value = state.get(key)
    state.delete(key)
    return value


def provide_wizard_input(state: BaseState, value: Any) -> str | None:
    """Route input using the active prompt bundle published by a phase."""
    prompt = state.get(WizardKeys.ACTIVE_PROMPT)
    if not isinstance(prompt, dict):
        return None
    input_key = prompt.get("input_key")
    if not isinstance(input_key, str):
        return None
    state.set(input_key, value)
    slug = prompt.get("slug")
    return str(slug) if slug is not None else None


def activate_prompt(
    state: BaseState,
    *,
    ctx: WizardPhaseContext,
    bundle: dict[str, Any],
    event_type: str | None = None,
    **event_payload: Any,
) -> None:
    """Publish prompt metadata and record step position for a phase."""
    prompt_key = wizard_prompt_key(ctx.step.slug)
    bundle.setdefault("input_key", wizard_input_key(ctx.step.slug))
    set_step_position(state, slug=ctx.step.slug, index=ctx.step_index)
    publish_prompt(state, prompt_key=prompt_key, bundle=bundle)
    if event_type is not None:
        emit_wizard_event(
            ctx.emit,
            ctx.wizard_name,
            event_type,
            slug=ctx.step.slug,
            title=bundle.get("title", ctx.step.title),
            step_index=ctx.step_index,
            **event_payload,
        )


def build_phase_prompt(
    state: BaseState,
    ctx: WizardPhaseContext,
    **extra: Any,
) -> dict[str, Any]:
    return build_prompt_bundle(
        state,
        wizard_name=ctx.wizard_name,
        step=ctx.step,
        step_index=ctx.step_index,
        context=ctx.context_engine,
        input_key=wizard_input_key(ctx.step.slug),
        **extra,
    )


def clear_phase_prompt(state: BaseState, step_slug: str) -> None:
    clear_active_prompt(state, prompt_key=wizard_prompt_key(step_slug))


def enter_phase_scope(state: BaseState, ctx: WizardPhaseContext) -> None:
    enter_wizard_step(
        state,
        ctx.step,
        index=ctx.step_index,
        context=ctx.context_engine,
    )


def is_affirmative(value: Any) -> bool:
    return value in (True, "yes", "Yes", "YES")