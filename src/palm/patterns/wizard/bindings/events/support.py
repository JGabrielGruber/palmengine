"""
Shared helpers for wizard behavior-tree leaves.

Centralizes step positioning, prompt publishing, and event emission so leaf
implementations stay thin and composable with Palm core primitives.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from palm.core.context import BaseState, ContextEngine
from palm.patterns.wizard.bindings.context.keys import WizardKeys
from palm.patterns.wizard.bindings.context.state import enrich_prompt_bundle, enter_step, leave_step
from palm.patterns.wizard.bindings.definitions.config import WizardStepConfig

EventEmitter = Callable[[str, dict[str, Any]], None]


def set_step_position(state: BaseState, *, slug: str, index: int) -> None:
    """Record the active wizard step for UI, persistence, and resume."""
    state.set(WizardKeys.CURRENT_STEP, slug)
    state.set(WizardKeys.STEP_INDEX, index)


def publish_prompt(state: BaseState, *, prompt_key: str, bundle: dict[str, Any]) -> None:
    """Publish prompt metadata for CLI, server, and ``provide_input`` routing."""
    state.set(prompt_key, bundle)
    state.set(WizardKeys.ACTIVE_PROMPT, bundle)


def clear_active_prompt(state: BaseState, *, prompt_key: str | None = None) -> None:
    """Clear active prompt state after a step completes or fails."""
    if prompt_key is not None:
        state.delete(prompt_key)
    state.delete(WizardKeys.ACTIVE_PROMPT)


def build_prompt_bundle(
    state: BaseState,
    *,
    wizard_name: str,
    step: WizardStepConfig,
    step_index: int,
    context: ContextEngine | None = None,
    include_validation: bool = True,
    **extra: Any,
) -> dict[str, Any]:
    """Build a standard wizard prompt bundle with scope metadata."""
    bundle: dict[str, Any] = {
        "wizard": wizard_name,
        "slug": step.slug,
        "title": step.title,
        "prompt": step.prompt,
        "field_type": step.field_type,
        "choices": list(step.choices),
        "step_index": step_index,
        "step_kind": step.step_kind,
    }
    bundle.update(extra)
    return enrich_prompt_bundle(
        state,
        bundle,
        context=context,
        include_validation=include_validation,
    )


def enter_wizard_step(
    state: BaseState,
    step: WizardStepConfig,
    *,
    index: int,
    context: ContextEngine | None = None,
) -> None:
    """Set step position and enter the step scope."""
    set_step_position(state, slug=step.slug, index=index)
    enter_step(state, step.slug, step=step, context=context)


def leave_wizard_step(
    state: BaseState,
    step: WizardStepConfig,
    *,
    context: ContextEngine | None = None,
) -> None:
    """Exit the step scope after successful completion."""
    leave_step(state, step.slug, context=context)


def emit_wizard_event(
    emit: EventEmitter | None,
    wizard_name: str,
    event_type: str,
    **payload: Any,
) -> None:
    """Emit a wizard event when an emitter is configured."""
    if emit is None:
        return
    payload.setdefault("wizard", wizard_name)
    emit(event_type, payload)
