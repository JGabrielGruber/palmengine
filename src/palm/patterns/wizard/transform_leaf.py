"""
WizardTransformLeaf — apply transform rules inside a wizard sequence.
"""

from __future__ import annotations

from typing import Any

from palm.common.transforms.builder import build_transform_leaf
from palm.common.transforms.execution import TransformExecutor
from palm.common.transforms.preview import preview_value
from palm.core.behavior_tree import LeafNode, PatternStatus
from palm.core.behavior_tree.nodes.leaf.transform_leaf import TransformLeaf
from palm.core.context import BaseState
from palm.core.resource import ResourceEngine
from palm.core.transform.engine import _MISSING
from palm.patterns.wizard.config import WizardStepConfig
from palm.patterns.wizard.events import WizardEventType
from palm.patterns.wizard.keys import WizardKeys
from palm.patterns.wizard.state import (
    enrich_prompt_bundle,
    enter_step,
    get_answers,
    leave_step,
    set_answers,
)
from palm.patterns.wizard.step_leaf import EventEmitter
from palm.patterns.wizard.validation import (
    clear_validation_feedback,
    publish_validation_feedback,
)


def format_transform_label(step: WizardStepConfig) -> str:
    """Return a short rule/chain label for prompts and CLI feedback."""
    spec = step.transform
    if spec is None:
        return "transform"
    if spec.chain:
        return " → ".join(spec.chain)
    return spec.rule or "transform"


def default_transform_prompt(step: WizardStepConfig) -> str:
    """Build the default operator-facing prompt for a transform step."""
    spec = step.transform
    if spec is None:
        return "Applying transform"
    target = spec.target_key or spec.source_key
    return f"Applying transform: {format_transform_label(step)} " f"({spec.source_key} → {target})"


def format_transform_feedback(
    step: WizardStepConfig,
    *,
    result_preview: str | None = None,
    applied: bool = True,
) -> str:
    """Build CLI feedback after a transform step runs."""
    verb = "Applied" if applied else "Applying"
    spec = step.transform
    if spec is None:
        return f"{verb} transform"
    target = spec.target_key or spec.source_key
    base = f"{verb} transform: {format_transform_label(step)} ({spec.source_key} → {target})"
    if result_preview is not None:
        return f"{base} → {result_preview}"
    return base


class WizardTransformLeaf(LeafNode):
    """Runs a declarative transform via :class:`~palm.common.transforms.execution.TransformExecutor`."""

    PROMPT_KEY_PREFIX = "__bt_prompt__"

    def __init__(
        self,
        step: WizardStepConfig,
        *,
        wizard_name: str,
        step_index: int,
        emit: EventEmitter | None = None,
        context_engine: Any | None = None,
        executor: TransformExecutor | None = None,
        resource_engine: ResourceEngine | None = None,
    ) -> None:
        super().__init__(step.slug)
        if step.transform is None:
            raise ValueError(f"Transform step {step.slug!r} requires transform configuration")
        self._step = step
        self._wizard_name = wizard_name
        self._step_index = step_index
        self._emit = emit
        self._context = context_engine
        self._executor = executor or TransformExecutor()
        self._resource_engine = resource_engine
        self._inner = build_transform_leaf(
            step.transform,
            engine=self._executor.engine,
            resource_engine=resource_engine,
        )

    @property
    def step(self) -> WizardStepConfig:
        return self._step

    def prompt_key(self) -> str:
        return f"{self.PROMPT_KEY_PREFIX}:{self._step.slug}"

    def _read_source_value(self, state: BaseState) -> Any:
        spec = self._step.transform
        assert spec is not None
        return self._executor.engine.read_state_value(
            state,
            spec.source_key,
            scoped=spec.scoped,
            default=None,
        )

    def _prompt_bundle(
        self, state: BaseState, *, source_preview: str | None = None
    ) -> dict[str, Any]:
        spec = self._step.transform
        assert spec is not None
        bundle = {
            "wizard": self._wizard_name,
            "slug": self._step.slug,
            "title": self._step.title,
            "prompt": self._step.prompt or default_transform_prompt(self._step),
            "field_type": "transform",
            "step_kind": "transform",
            "step_index": self._step_index,
            "transform_rule": spec.rule,
            "transform_chain": list(spec.chain),
            "transform_source_key": spec.source_key,
            "transform_target_key": spec.target_key or spec.source_key,
            "transform_source_preview": source_preview,
        }
        return enrich_prompt_bundle(
            state,
            bundle,
            context=self._context,
            include_validation=False,
        )

    def _tick_impl(self, state: BaseState) -> PatternStatus:
        spec = self._step.transform
        assert spec is not None

        state.set(WizardKeys.CURRENT_STEP, self._step.slug)
        state.set(WizardKeys.STEP_INDEX, self._step_index)
        if spec.scoped:
            enter_step(state, self._step.slug, step=self._step, context=self._context)

        self._ensure_source_from_answers(state)
        source_value = self._read_source_value(state)
        source_preview = preview_value(source_value)
        prompt_bundle = self._prompt_bundle(state, source_preview=source_preview)
        state.set(self.prompt_key(), prompt_bundle)
        state.set(WizardKeys.ACTIVE_PROMPT, prompt_bundle)
        self._fire(
            WizardEventType.STEP_STARTED,
            slug=self._step.slug,
            title=self._step.title,
            step_index=self._step_index,
            step_kind="transform",
            source_preview=source_preview,
        )

        status = self._inner.tick(state)

        if status == PatternStatus.SUCCESS:
            result_value = self._read_result_value(state)
            result_preview = preview_value(result_value)
            self._persist_transform_result(state, result_value)
            if spec.scoped:
                leave_step(state, self._step.slug, context=self._context)
            state.delete(self.prompt_key())
            state.delete(WizardKeys.ACTIVE_PROMPT)
            clear_validation_feedback(state)
            feedback = format_transform_feedback(
                self._step,
                result_preview=result_preview,
            )
            state.set(WizardKeys.TRANSFORM_FEEDBACK, feedback)
            self._fire(
                WizardEventType.TRANSFORM_APPLIED,
                slug=self._step.slug,
                source_key=spec.source_key,
                target_key=spec.target_key or spec.source_key,
                rule=spec.rule,
                chain=list(spec.chain),
                step_index=self._step_index,
                source_preview=source_preview,
                result_preview=result_preview,
            )
            return PatternStatus.SUCCESS

        message = self._failure_message(state)
        prompt_bundle = self._prompt_bundle(state, source_preview=source_preview)
        prompt_bundle["transform_error"] = message
        publish_validation_feedback(
            state,
            (message,),
            prompt_bundle=prompt_bundle,
            prompt_key=self.prompt_key(),
        )
        self._fire(
            WizardEventType.VALIDATION_FAILED,
            slug=self._step.slug,
            errors=[message],
            step_kind="transform",
            source_preview=source_preview,
        )
        if spec.scoped:
            leave_step(state, self._step.slug, context=self._context)
        return PatternStatus.FAILURE

    def _ensure_source_from_answers(self, state: BaseState) -> None:
        """Promote prior step answers to blackboard keys transforms can read."""
        spec = self._step.transform
        assert spec is not None
        current = self._executor.engine.read_state_value(
            state,
            spec.source_key,
            scoped=spec.scoped,
            default=_MISSING,
        )
        if current is not _MISSING and current is not None:
            return
        answers = get_answers(state)
        if spec.source_key not in answers:
            return
        self._executor.engine.write_state_value(
            state,
            spec.source_key,
            answers[spec.source_key],
            scoped=spec.scoped,
            validate=False,
        )

    def _read_result_value(self, state: BaseState) -> Any:
        spec = self._step.transform
        assert spec is not None
        target = spec.target_key or spec.source_key
        return self._executor.engine.read_state_value(
            state,
            target,
            scoped=spec.scoped,
            default=None,
        )

    def _persist_transform_result(self, state: BaseState, value: Any) -> None:
        spec = self._step.transform
        assert spec is not None
        if value is None:
            return
        target = spec.target_key or spec.source_key
        answers = get_answers(state)
        answers[target] = value
        set_answers(state, answers)
        if state.schema is not None:
            state.set_validated(target, value)

    def _failure_message(self, state: BaseState) -> str:
        spec = self._step.transform
        assert spec is not None
        if spec.error_key:
            raw = state.get(spec.error_key)
            if raw is not None:
                return str(raw)
        trace_key = spec.trace_key or TransformLeaf.default_trace_key(spec.name)
        trace = state.get(trace_key)
        if isinstance(trace, dict):
            error = trace.get("error")
            if error is not None:
                return str(error)
        return (
            f"Transform {format_transform_label(self._step)!r} failed for "
            f"{spec.source_key!r} → {spec.target_key or spec.source_key!r}"
        )

    def _fire(self, event_type: str, **payload: Any) -> None:
        if self._emit is not None:
            payload.setdefault("wizard", self._wizard_name)
            self._emit(event_type, payload)
